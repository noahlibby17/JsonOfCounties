import bson, code, copy, csv, json, math, os, re

from scipy.ndimage import filters
import shapefile

import matplotlib.pyplot as plt
import numpy as np

import os

pjoin = os.path.join

# pip install Shapely
from shapely import geometry
from shapely.geometry import Point

def pad(t, n, c=' '):
	t = str(t)
	return max(n - len(t), 0) * c + t

abbreviation_to_name = {
	"AL": "Alabama",
	"AK": "Alaska",
	"AZ": "Arizona",
	"AR": "Arkansas",
	"CA": "California",
	"CO": "Colorado",
	"CT": "Connecticut",
	"DE": "Delaware",
	"DC": "District of Columbia",
	"FL": "Florida",
	"GA": "Georgia",
	"GU": "Guam",
	"HI": "Hawaii",
	"ID": "Idaho",
	"IL": "Illinois",
	"IN": "Indiana",
	"IA": "Iowa",
	"KS": "Kansas",
	"KY": "Kentucky",
	"LA": "Louisiana",
	"ME": "Maine",
	"MD": "Maryland",
	"MA": "Massachusetts",
	"MI": "Michigan",
	"MN": "Minnesota",
	"MS": "Mississippi",
	"MO": "Missouri",
	"MT": "Montana",
	"NE": "Nebraska",
	"NV": "Nevada",
	"NH": "New Hampshire",
	"NJ": "New Jersey",
	"NM": "New Mexico",
	"NY": "New York",
	"NC": "North Carolina",
	"ND": "North Dakota",
	"OH": "Ohio",
	"OK": "Oklahoma",
	"OR": "Oregon",
	"PA": "Pennsylvania",
	"RI": "Rhode Island",
	"SC": "South Carolina",
	"SD": "South Dakota",
	"TN": "Tennessee",
	"TX": "Texas",
	"UT": "Utah",
	"VT": "Vermont",
	"VI": "Virgin Islands",
	"VA": "Virginia",
	"WA": "Washington",
	"WV": "West Virginia",
	"WI": "Wisconsin",
	"WY": "Wyoming",
}

fips_code_to_name = {
	"01": "Alabama",
	"02": "Alaska",
	"04": "Arizona",
	"05": "Arkansas",
	"06": "California",
	"08": "Colorado",
	"09": "Connecticut",
	"10": "Delaware",
	"11": "District of Columbia",
	"12": "Florida",
	"13": "Georgia",
	"15": "Hawaii",
	"16": "Idaho",
	"17": "Illinois",
	"18": "Indiana",
	"19": "Iowa",
	"20": "Kansas",
	"21": "Kentucky",
	"22": "Louisiana",
	"23": "Maine",
	"24": "Maryland",
	"25": "Massachusetts",
	"26": "Michigan",
	"27": "Minnesota",
	"28": "Mississippi",
	"29": "Missouri",
	"30": "Montana",
	"31": "Nebraska",
	"32": "Nevada",
	"33": "New Hampshire",
	"34": "New Jersey",
	"35": "New Mexico",
	"36": "New York",
	"37": "North Carolina",
	"38": "North Dakota",
	"39": "Ohio",
	"40": "Oklahoma",
	"41": "Oregon",
	"42": "Pennsylvania",
	"44": "Rhode Island",
	"45": "South Carolina",
	"46": "South Dakota",
	"47": "Tennessee",
	"48": "Texas",
	"49": "Utah",
	"50": "Vermont",
	"51": "Virginia",
	"53": "Washington",
	"54": "West Virginia",
	"55": "Wisconsin",
	"56": "Wyoming",
	"60": "American Samoa",
	"66": "Guam",
	"69": "Northern Mariana Islands",
	"72": "Puerto Rico",
	"78": "Virgin Islands",
}

not_states = set([
	"American Samoa",
	"Guam",
	"Northern Mariana Islands",
	"Puerto Rico",
	"Virgin Islands",
])

# Converts '7/13/20' to '2020-07-13'
def date_to_ymd(t):
	m, d, y = t.split('/')
	return f"20{y}-{pad(m, 2, c='0')}-{pad(d, 2, c='0')}"

# Maps formly independent cities to the counties they
# now belong to.  This way we can add the deaths from
# these cities (which the CDC keeps separate, since its
# data goes back to 1999) to the counties the cities
# now belong to.
former_independent_cities_to_counties = {
	"Virginia": {
		"clifton forge city": "alleghany county",
		"bedford city": "bedford county",
	}
}

class CountyNameMerger:
	kHardCoded = {
		"Alabama": {
			"de kalb": "dekalb county",	
		},
		"Alaska": {
			"anchorage borough": "anchorage municipality",
			"juneau borough": "juneau city and borough",
			"petersburg borough/census area": "petersburg borough",
			"sitka borough": "sitka city and borough",
			"skagway-hoonah-angoon census area" : "skagway municipality",
			"wrangell-petersburg census area": "wrangell city and borough",
			"yakutat borough": "yakutat city and borough",
			# Formerly known as Wade Hampton Census Area
			"wade hampton census area": "kusilvak census area",
			# Renamed in 2008
			"prince of wales-outer ketchikan census area": "prince of wales-hyder census area",

			"anchorage borough/municipality": "anchorage municipality",
			"juneau borough/city": "juneau city and borough",
			"sitka borough/city": "sitka city and borough",
			"wrangell borough/city": "wrangell city and borough",
			"yakutat borough/city": "yakutat city and borough",

			"municipality of anchorage": "anchorage municipality",
			"city and borough of juneau": "juneau city and borough",
			"petersburg census area": "petersburg borough",
		},
		"California": {
			"san francisco county/city": "san francisco county",
		},
		"Colorado": {
			"broomfield county/city": "broomfield county",
		},
		"District of Columbia": {
			"washington": "district of columbia",
			"district of columbia county": "district of columbia",
		},
		"Florida": {
			"de soto": "desoto county",
		},
		"Georgia": {
			"de kalb": "dekalb county",
		},
		"Idaho": {
			"fremont (includes yellowstone park)": "fremont county"
		},
		"Illinois": {
			"la salle": "lasalle county",
			"du page": "dupage county",
			"de kalb": "dekalb county",
		},
		"Indiana": {
			"de kalb": "dekalb county",
			"de kalb county": "dekalb county",
			"la porte county": "laporte county",
			"la porte": "laporte county",
			"de kalb": "dekalb county",
			"la grange": "lagrange county",
		},
		"Iowa": {
			"o brien": "o'brien county",
		},
		"Louisiana": {
			"la salle parish": "lasalle parish",
			"la salle": "lasalle parish",
		},
		"Maryland": {
			"baltimore (independent city)": "baltimore city",
			"baltimore city county": "baltimore city",
			"prince georges": "prince george's county",
			"queen annes": "queen anne's county",
			"st. marys": "st. mary's county",
		},
		"Mississippi": {
			"de soto": "desoto county",
		},
		"Missouri": {
			"jackson county (including other portions of kansas city)": "jackson county",
			"city of st. louis": "st. louis city",
			"st. louis city county": "st. louis city",
			"Jackson County (including other portions of Kansas City)": "Jackson County",
			"de kalb": "dekalb county",
		},
		"Nevada": {
			"carson city county": "carson city"
		},
		"New Mexico": {
			"debaca county": "de baca county",
			"dona ana county": "doña ana county",
			"dona ana": "doña ana county",
		},
		"North Dakota": {
			"la moure": "lamoure county",
		},
		"Pennsylvania": {
			"mc kean county": "mckean county",
		},
		"South Dakota": {
			"shannon county": "oglala lakota county",
			"shannon": "oglala lakota county",
		},
		"Tennessee": {
			"de kalb": "dekalb county",	
		},
		"Texas": {
			"de witt": "dewitt county",
		},
		"Virginia": {
			"colonial heights cit": "colonial heights city"
		}
	}


# if county not in states[state] and county + ' county' in states[state]:
# 	county = county + ' county'
# if county not in states[state] and county + ' parish' in states[state]:
# 	county = county + ' parish'
# assert county in states[state], f'{county}, {state}'


	def __init__(self):
		with open('base.json', 'r') as f:
			self.states = json.load(f)

	def merge_state(self, state, list1, list2, allow_missing, missing):
		if (not allow_missing) and len(missing.get(state, {})) == 0:
			assert len(list1) == len(list2), f"{state}\n\n{sorted(list1)}\n\n{sorted(list2)}"
			assert len(set(list1)) == len(list1)
			assert len(set(list2)) == len(list2)

		hardCoded = CountyNameMerger.kHardCoded.get(state, {})

		M = {}

		i = 0
		while i < len(list1):
			county = list1[i].lower()
			if county[:3] == 'st ':
				county = 'st. ' + county[3:]

			if county[-19:] == ' (independent city)':
				if county[-23:-18] != 'city ':
					county = county[:-19] + ' city'
				else:
					county = county[:-19]

			if county[-12:] == ' county/city':
				county = county[:-5]
			if county[-12:] == ' county/town':
				county = county[:-5]

			if county in hardCoded:
				j = list2.index(hardCoded[county])
				M[list1[i]] = list2[j]
				del list1[i]
				del list2[j]
			elif county in list2:
				j = list2.index(county)
				M[list1[i]] = list2[j]
				del list1[i]
				del list2[j]
			elif county + ' county' in list2:
				j = list2.index(county + ' county')
				M[list1[i]] = list2[j]
				del list1[i]
				del list2[j]
			elif state == 'Louisiana' and county + ' parish' in list2:
				j = list2.index(county + ' parish')
				M[list1[i]] = list2[j]
				del list1[i]
				del list2[j]
			else:
				i += 1

		list1.sort()
		list2.sort()

		if state not in missing:
			assert len(list1) == 0, f"{state}\n\n{list1}\n\n{list2}"
		else:
			assert len([x for x in list1 if x not in missing[state]]) == 0

		if not allow_missing:
			assert len(list2) - len(missing.get(state, {})) == 0, list2

		# Assert mapping is not many-to-1
		assert len(M.values()) == len(set(M.values()))

		return M

	def merge(self, states, allow_missing=False, missing={}):
		if not allow_missing:
			assert len(states) == 51
		for state in states:
			M = self.merge_state(
				state,
				list(states[state].keys()),
				list(self.states[state].keys()),
				allow_missing=allow_missing,
				missing=missing
			)
			for county in M:
				self.add_to_json(
					self.states[state][M[county]],
					states[state][county]
				)

	def add_to_json(self, base, addition):
		for k in addition:
			assert k not in base
			base[k] = addition[k]

def get_geometry():
	states = {}

	sf = shapefile.Reader(pjoin('data', 'tl_2017_us_county/tl_2017_us_county.shp'))

	# Add geometric data for countries.
	for s in sf:
		state = fips_code_to_name[s.record.STATEFP]
		if state in not_states:
			continue
		if state not in states:
			states[state] = {}
		county_name = s.record.NAMELSAD.lower()

		# There is one county that crosses from negative
		# to positive longitudes, which screws up center-point
		# computations.  To fix this we subtact 360 from
		# positive longitudes.
		poly = geometry.Polygon([(x - 360 if x > 0 else x, y) for x, y in s.shape.points])

		# We explicitly compute centroids rather than use
		# s.record.INTPTLAT and s.record.INTPTLON, since
		# I can't find any documentation of how these
		# points are actually picked.  We use the convex
		# hull since some 'polygons' are weird, due to some
		# islands containing islands of territory (figuratively
		# and literally).
		center = poly.convex_hull.centroid

		states[state][county_name] = {
			"land_area": s.record.ALAND / 1e6,
			"area": (s.record.ALAND + s.record.AWATER) / 1e6,

			# NOTE: we don't undo the "- 360" transformation
			# above, since most use cases probably *prefer*
			# not having to deal with the wrapping behavior.
			"longitude": center.x,
			"latitude": center.y,
		}

	return states

def get_zips():
	states = {}
	with open(pjoin('data', 'zip_county_fips_2018_03.csv'), 'r') as f:
		reader = csv.reader(f, delimiter=',')
		header = next(reader)
		rows = [row for row in reader]

	for zipcode, fips, city, state, county, _ in rows:
		if state in ["PR", "GU", "VI"]:
			continue
		state = abbreviation_to_name[state]
		county = county.lower()
		if state not in states:
			states[state] = {}
		if county not in states[state]:
			states[state][county] = {
				'zip-codes': []
			}
		states[state][county]['zip-codes'].append(zipcode)

	states["Alaska"]["kusilvak census area"] = {
		"zip-codes": [
			"99554", "99563", "99581", "99585", "99604", "99620", "99632", "99650", "99657", "99658", "99662", "99666"
		]
	}
	states["South Dakota"]["oglala lakota county"] = {
		"zip-codes": [
			"57716", "57752", "57756", "57764", "57770", "57772", "57794",
		]
	}
	return states

def get_demographics():
	age_code_to_group = {
	  0: "all",
		1: "0-4",
		2: "5-9",
		3: "10-14",
		4: "15-19",
		5: "20-24",
		6: "25-29",
		7: "30-34",
		8: "35-39",
		9: "40-44",
		10: "45-49",
		11: "50-54",
		12: "55-59",
		13: "60-64",
		14: "65-69",
		15: "70-74",
		16: "75-79",
		17: "80-84",
		18: "85+"
	}

	# https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2018/cc-est2018-alldata.pdf
	year_code_to_year = {
		 "1": "4/1/2010",
		 "2": "4/1/2010", # sic
		 "3": "7/1/2010",
		 "4": "7/1/2011",
		 "5": "7/1/2012",
		 "6": "7/1/2013",
		 "7": "7/1/2014",
		 "8": "7/1/2015",
		 "9": "7/1/2016",
		"10": "7/1/2017",
		"11": "7/1/2018",
	}
	# After downloading this file you should open it with a text editor (
	# I use Sublime) and re-encode it as utf8.

	states = {}

	with open(pjoin('data', 'cc-est2018-alldata.csv'), 'r') as f:
		reader = csv.reader(f, delimiter=',')
		header = next(reader)
		rows = [row for row in reader]
		assert header[:7] == ['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'YEAR', 'AGEGRP']
		for row in rows:
			state = row[3]
			if state not in states:
				states[state] = {}

			county = row[4].lower()

			# We only grab the latest year available and ignore the
			# other rows.
			if year_code_to_year[row[5]] != '7/1/2018':
				continue

			age_group = int(row[6])
			if age_group == 0:
				# age group "0" is everyone.  We grab racial data from
				# this row.  The racial break down done by the Census
				# Bureau is... intense, with 73 different columns.  To
				# keep the file size reasonable I don't track them all.
				# Fortunately the code and data is freely available so
				# it is trivial for you to add more columns if you like!

				# We assume this is the first row we see.
				assert county not in states[state]
				states[state][county] = {}
				states[state][county]['race_demographics'] = {}
				states[state][county]['age_demographics'] = {}

				states[state][county]['male'] = int(row[8])
				states[state][county]['female'] = int(row[9])

				total = int(row[7])
				states[state][county]['population'] = total

				states[state][county]['race_demographics']['non_hispanic_white_alone_male'] = int(row[34]) / total
				states[state][county]['race_demographics']['non_hispanic_white_alone_female'] = int(row[35]) / total

				states[state][county]['race_demographics']['black_alone_male'] = int(row[12]) / total
				states[state][county]['race_demographics']['black_alone_female'] = int(row[13]) / total

				states[state][county]['race_demographics']['asian_alone_male'] = int(row[16]) / total
				states[state][county]['race_demographics']['asian_alone_female'] = int(row[17]) / total

				states[state][county]['race_demographics']['hispanic_male'] = int(row[56]) / total
				states[state][county]['race_demographics']['hispanic_female'] = int(row[57]) / total

			else:
				states[state][county]['age_demographics'][age_code_to_group[int(row[6])]] = int(row[7]) / states[state][county]['population']

			assert county in states[state]

	for state_name in states:
		for county_name in states[state_name]:
			assert 'race_demographics' in states[state_name][county_name]

	return states

def get_cdc_deaths():
	states = {}
	for varname, fn in zip(['suicides', 'firearm suicides', 'homicides'], ["Compressed Mortality, 1999-2016 (all suicides).txt", "Compressed Mortality, 1999-2016 (firearm suicides).txt", "Compressed Mortality (assaults), 1999-2016.txt"]):
		with open(pjoin('data', fn), 'r') as f:
			reader = csv.reader(f, delimiter='\t', quotechar='"')
			rows = [row for row in reader]
		header = rows[0]
		rows = rows[1:]
		rows = rows[:rows.index(['---']) - 1]
		former_independent_cities = {}
		for row in rows:
			_, county, _, deaths, _, _ = row
			county = county.lower()
			state = abbreviation_to_name[county.split(', ')[-1].upper()]
			if state not in states:
				states[state] = {}
			county = ', '.join(county.split(', ')[:-1])

			# These counties changed their names recently, and rows with
			# both the old names and new names are found in the CDC
			# dataset, so we simply ignore these names.
			if county in ['prince of wales-outer ketchikan census area', 'skagway-hoonah-angoon census area', "wrangell-petersburg census area"]:
				continue

			if deaths == 'Suppressed':
				deaths = None
			else:
				deaths = int(deaths)

			if state in former_independent_cities_to_counties and county in former_independent_cities_to_counties[state]:
				county = former_independent_cities_to_counties[state][county]
				if state not in former_independent_cities:
					former_independent_cities[state] = {}
				former_independent_cities[state][county] = deaths
				continue

			if county not in states[state]:
				states[state][county] = {
					"deaths": {}
				}
			assert varname not in states[state][county]
			states[state][county]["deaths"][varname] = deaths

		# Add formly independent cities to their respective counties.
		for state in former_independent_cities:
			for county in former_independent_cities[state]:
				# If either value was suppressed, we keep the concatenated
				# value as None.
				if states[state][county]["deaths"][varname] is None:
					continue
				if former_independent_cities[state][county] is None:
					continue
				states[state][county]["deaths"][varname] += former_independent_cities[state][county]

		for state in states:
			for county in states[state]:
				assert varname in states[state][county]["deaths"]

	return states

# Labor force data
# https://www.bls.gov/lau/#cntyaa

def get_labor_force():
	states = {}

	with open(pjoin('data', 'laborforce.txt'), 'r') as f:
		lines = f.readlines()
		for line in lines[6:]:
			line = line.strip()
			if len(line) == 0:
				break
			laus_code, state_fips_code, county_fips_code, county_name, year, labor_force, employed, unemployed, unemployment_rate = re.sub(r"  +", "  ", line).split("  ")

			if county_name == "District of Columbia":
				state = "District of Columbia"
				county_name = state.lower()
			else:
				state = county_name.split(', ')[-1]
				if state not in abbreviation_to_name:
					continue
				state = abbreviation_to_name[state]
				county_name = ', '.join(county_name.split(', ')[:-1]).lower()

			if state in not_states:
				continue

			if state not in states:
				states[state] = {}

			county = {}
			county['labor_force'] = float(labor_force.replace(",",""))
			county['employed'] = float(employed.replace(",",""))
			county['unemployed'] = float(unemployed.replace(",",""))
			county['unemployment_rate'] = float(unemployment_rate)
			assert county_name not in states[state]
			states[state][county_name] = county

	# Missing county...
	assert "kalawao county" not in states["Hawaii"]
	states["Hawaii"]["kalawao county"] = {
		"labor_force": None,
		"employed": None,
		"unemployed": None,
		"unemployment_rate": None
	}

	return states

def get_fatal_police_shootings():
	states = {}
	for year in ['2017', '2018', '2019']:
		for varname in [f'total-{year}', f'unarmed-{year}', f'firearmed-{year}']:
			with open(pjoin('generated', 'police_shootings', varname + '.json'), 'r') as f:
				shootings = json.load(f)

				for k in shootings:
					state_name = abbreviation_to_name[k[-2:].upper()]
					if state_name not in states:
						states[state_name] = {}
					state = states[state_name]
					county_name = k[:-4]

					if county_name not in state:
						state[county_name] = {
							"fatal_police_shootings": {}
						}

					state[county_name]["fatal_police_shootings"][varname] = shootings[k]

	return states

def get_police_deaths():
	states = {}

	with open(pjoin('data', 'police-deaths-2019.txt'), 'r') as f:
		lines = f.readlines()[8:]
	lines = [line.strip() for line in lines]
	F = {}
	for i in range(0, len(lines), 5):
		name = lines[i + 0]
		cause = lines[i + 2]
		F[cause] = F.get(cause, 0) + 1
		location = lines[i + 3]
		state = abbreviation_to_name[location[-2:]]
		county = location[:-4].lower()
		if state not in states:
			states[state] = {}
		if county not in states[state]:
			states[state][county] = {}
		states[state][county]['police_deaths'] = states[state][county].get('police_deaths', 0) + 1

	return states

def get_avg_income():
	states = {}
	for fn in os.listdir(pjoin('data', 'CAINC1')):
		with open(pjoin('data', 'CAINC1', fn), 'r', encoding='Latin-1') as f:
			reader = csv.reader(f, delimiter=',')
			header = next(reader)
			rows = [row for row in reader]
			for row in rows[3:-1]:
				if len(row) < 7:
					continue

				if row[6] != 'Per capita personal income (dollars) 2/':
					continue

				# This is an effective way to ensure the row is
				# sensible (and not a footer / footnote).
				try:
					avg_income = int(row[-1])
				except ValueError:
					continue

				loc = row[1]
				# ignore fotenotes...
				while loc[-1] == '*':
					loc = loc[:-1]
				assert loc[-4:-2] == ', '
				county = loc[:-4].lower()
				state = abbreviation_to_name[loc[-2:]]

				if state not in states:
					states[state] = {}

				# These counties are combined...
				if loc == 'Maui + Kalawao, HI':
					assert "maui county" not in states[state]
					assert "kalawao county" not in states[state]
					states[state]['maui county'] = {
						"avg_income": avg_income
					}
					states[state]['kalawao county'] = {
						"avg_income": avg_income
					}
					continue

				# Independent cities are merged with their surrounding counties.
				# We un-merge them here.
				if '+' in county:
					parts = [x.strip() for x in re.findall(r"[^,\+]+", county)]
					assert parts[0] + ' county' not in states[state]
					states[state][parts[0] + ' county'] = {
						"avg_income": avg_income
					}
					for part in parts[1:]:
						if part[-5:] != ' city':
							part += ' city'
						assert part not in states[state]
						states[state][part] = {}
						states[state][part]['avg_income'] = avg_income
					continue

				assert county not in states[state]
				states[state][county] = {
					"avg_income": avg_income
				}

	for state in states:
		for county in states[state]:
			assert 'avg_income' in states[state][county]

	return states

def get_covid():
	blacklist = {
		"Alaska": {
			# Ordinarily we'd map this to "kusilvak census area" but,
			# (I assume due to an oversight by either the CDC or
			# usafacts.org) this county represented twice (once for
			# each name).  Fortunately both death counts are zero, so
			# we just ignore it for now.
			"wade hampton census area": None,
		},
		"California": {
			"grand princess cruise ship": None,
		},
	}

	states = {}

	for varname, fn in zip(['deaths', 'confirmed'], ['covid_deaths_usafacts.csv', 'covid_confirmed_usafacts.csv']):
		with open(pjoin('data', fn), 'r') as f:
			reader = csv.reader(f, delimiter=',')
			header = next(reader)
			rows = [row for row in reader]
			for date in ['5/4/20', '5/11/20', '5/18/20', '5/25/20', '6/1/20', '6/8/20', '6/15/20', '6/22/20', '6/29/20', '7/6/20', '7/13/20', '7/20/20', '7/27/20', '8/3/20', '8/10/20', '8/17/20', '8/24/20']:
				column = header.index(date)
				new_york_unallocated = 0
				for row in rows:
					if row[1] == 'Statewide Unallocated':
						continue
					county = row[1].lower()
					state = abbreviation_to_name[row[2]]

					if state not in states:
						states[state] = {}

					# Lacking any clear/easy alternatives, we simply dump
					# these in New York County at the end of the loop.
					# We assert that the number of unallocated deaths is
					# pretty small.  If it ever becomes large (relative
					# to the New York counties) we may want to revisit
					# our approach.
					if county == "new york city unallocated/probable":
						new_york_unallocated = int(row[column])
						assert new_york_unallocated < 1500, new_york_unallocated
						continue

					# Apparently this dataset isn't consistent between its own CSV files, so
					# we need to hard-code some fixes...
					if state == 'Colorado' and county == "broomfield county and city":
						county = 'broomfield county'
					if state == 'Virginia' and county == "matthews county":
						county = "mathews county"


					if state == 'Alaska':
						if county == "wade hampton census area":
							wade_hampton = int(row[column])
						elif county == "kusilvak census area":
							kusilvak = int(row[column])

					if state in blacklist and county in blacklist[state]:
						continue

					if county not in states[state]:
						states[state][county] = {}

					if f"covid-{varname}" not in states[state][county]:
						states[state][county][f"covid-{varname}"] = {}

					datekey = date_to_ymd(date)
					assert datekey not in states[state][county][f"covid-{varname}"]
					states[state][county][f"covid-{varname}"][datekey] = int(row[column])

				# We distribute "unattributed New York deaths" proportional to how the other
				# covid deaths are distributed.
				total = states['New York']['new york county'][f"covid-{varname}"][datekey] + states['New York']['bronx county'][f"covid-{varname}"][datekey] + states['New York']['kings county'][f"covid-{varname}"][datekey] + states['New York']['queens county'][f"covid-{varname}"][datekey] + states['New York']['richmond county'][f"covid-{varname}"][datekey]
				if total > 0:
					states['New York']['new york county'][f"covid-{varname}"][datekey] += new_york_unallocated * (states['New York']['new york county'][f"covid-{varname}"][datekey] / total)
					states['New York']['bronx county'][f"covid-{varname}"][datekey] += new_york_unallocated * (states['New York']['bronx county'][f"covid-{varname}"][datekey] / total)
					states['New York']['kings county'][f"covid-{varname}"][datekey] += new_york_unallocated * (states['New York']['kings county'][f"covid-{varname}"][datekey] / total)
					states['New York']['queens county'][f"covid-{varname}"][datekey] += new_york_unallocated * (states['New York']['queens county'][f"covid-{varname}"][datekey] / total)
					states['New York']['richmond county'][f"covid-{varname}"][datekey] += new_york_unallocated * (states['New York']['richmond county'][f"covid-{varname}"][datekey] / total)

	# Wade Hampton and Kusilvak are the same cuonty but, for some reason, exist as two rows.
	# Hopefuly this is just an oversight and wade_hampton deaths are simply being counted as
	# kusilvak deaths.  But if wade_hampton deaths are ever non-zer we may want to email the
	# CDC and ask why they have duplicate rows.
	assert wade_hampton == 0, 'If this is ever violated, we need to revisit how we resolve these duplicate rows'

	return states

def get_elections():
	states = {}
	fips_to_county = {
		'08014': ('broomfield county', 'Colorado')
	}
	with open(pjoin('data', 'fips_to_county.txt'), 'r') as f:
		for line in f.readlines():
			if len(line.strip()) == 0:
				continue
			code, county, state = line.strip().split('\t')
			# American Samoa, Northern Mariana Islands, Puerto Rico
			if state in ['AS', 'MP', 'PR']:
				continue
			fips_to_county[code] = (county.lower(), abbreviation_to_name[state])

	with open(pjoin('data', 'US_County_Level_Presidential_Results_08-16.csv'), 'r') as f:
		reader = csv.reader(f, delimiter=',')
		header = next(reader)
		assert header == ['fips_code', 'county', 'total_2008', 'dem_2008', 'gop_2008', 'oth_2008', 'total_2012', 'dem_2012', 'gop_2012', 'oth_2012', 'total_2016', 'dem_2016', 'gop_2016', 'oth_2016']
		rows = [row for row in reader]
		for row in rows:
			county, state = fips_to_county[row[0]]

			if state not in states:
				states[state] = {}

			all2008 = int(row[2])
			dem2008 = int(row[3])
			gop2008 = int(row[4])

			all2012 = int(row[6])
			dem2012 = int(row[7])
			gop2012 = int(row[8])

			all2016 = int(row[10])
			dem2016 = int(row[11])
			gop2016 = int(row[12])

			states[state][county] = {
				"elections": {
					"2008": {
						"total": all2008,
						"dem": dem2008,
						"gop": gop2008,
					},
					"2012": {
						"total": all2012,
						"dem": dem2012,
						"gop": gop2012,
					},
					"2016": {
						"total": all2016,
						"dem": dem2016,
						"gop": gop2016,
					}
				},
				"fips": row[0]
			}

	# Missing Alaska
	assert "Alaska" not in states
	states["Alaska"] = {}

	return states

def add_weather(states):
	"""
	Value flags (which we ignore):
    C = complete (all 30 years used)
    S = standard (no more than 5 years missing and no more than 3 consecutive 
        years missing among the sufficiently complete years)
    R = representative (observed record utilized incomplete, but value was scaled
        or based on filled values to be representative of the full period of record)
    P = provisional (at least 10 years used, but not sufficiently complete to be 
        labeled as standard or representative). Also used for parameter values on 
        February 29 as well as for interpolated daily precipitation, snowfall, and
        snow depth percentiles. 
    Q = quasi-normal (at least 2 years per month, but not sufficiently complete to 
        be labeled as provisional or any other higher flag code. The associated
        value was computed using a pseudonormals approach or derived from monthly
        pseudonormals.
	"""
	stations = {}
	for varname, fn in [
			("prcp", "ann-prcp-normal.txt"),
			("snow", "ann-snow-normal.txt"),
			("temp", "ann-tavg-normal.txt"),
		]:
		with open(pjoin("data", "noaa-weather", fn), "r") as f:
			for line in f.readlines():
				station, val = re.split(r" +", line.strip())
				assert val[-1] in "CSRPQ", repr(val)
				val = float(val[:-1])
				if station not in stations:
					stations[station] = {}
				if varname == "prcp":
					stations[station][varname] = val / 100.0
				elif varname == "snow":
					stations[station][varname] = val / 10.0
				else:
					stations[station][varname] = val / 10.0

	# Read station locations
	with open(pjoin("data", "noaa-weather", "ghcnd-stations.txt"), "r") as f:
		lines = f.readlines()
		# Filter out stations that don't give us any data.
		lines = [line for line in lines if line.split(' ')[0] in stations]
		# station, latitude, longitude, elevation, ...
		lines = [re.split(r" +", line.strip()) for line in lines]
	station_locations = [(float(line[1]), float(line[2])) for line in lines]
	station_locations = np.array(station_locations)

	for state_name in states:
		state = states[state_name]
		for county_name in state:
			county = state[county_name]
			county["noaa"] = {}
			loc = np.array([county["latitude"], county["longitude"]])
			d = ((station_locations - loc)**2).sum(1)
			# Iterate through stations in order of their distance until
			# we find a value for every variable.
			for i in np.argsort(d):
				name = lines[i][0]
				if name not in stations:
					continue
				station = stations[name]
				for varname in station:
					if varname not in county["noaa"]:
						county["noaa"][varname] = station[varname]
				if len(county["noaa"]) >= 3:
					break

daysBeforeMonth = [
	0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
]
daysBeforeMonth = np.cumsum(daysBeforeMonth)

def get_mobility():
	with open(pjoin('data', 'applemobilitytrends-2020-08-29.csv'), 'r') as f:
		reader = csv.reader(f, delimiter=',')
		header = next(reader)
		rows = [row for row in reader]
	rows = [r for r in rows if r[5] == 'United States' and r[0] == 'county']
	rows = [[r[2], r[1], r[4]] + r[6:] for r in rows]

	X = header[6:]

	states = {}
	for row in rows:
		mode, county, state = row[:3]
		if state in ['Puerto Rico', 'Guam', 'Virgin Islands']:
			continue
		r = row[3:]
		Y = []
		for i in range(len(r)):
			if len(r[i]) > 0:
				Y.append(float(r[i]))
			elif len(r[i-1]) > 0:
				Y.append(float(r[i - 1]))
			else:
				Y.append(float(r[i + 1]))
		# import code; code.interact(local=locals())
		if state not in states:
			states[state] = {}
		if county not in states[state]:
			states[state][county] = {}
		if mode not in states[state][county]:
			states[state][county][mode] = {}
		Y = filters.uniform_filter(Y, 14)
		for x, y in zip(X[::14], Y[::14]):
			states[state][county][mode][x] = round(int(y))

	return states


if __name__ == '__main__':
	merger = CountyNameMerger()

	merger.merge(get_geometry())

	add_weather(merger.states)

	A = []
	states = {}
	sf = shapefile.Reader(pjoin('data', 'SpatialJoin_CDs_to_Counties_Final.shp'))
	for i, s in enumerate(sf):
		if s.record.STATE_NAME not in states:
			states[s.record.STATE_NAME] = {}
		r = s.record
		states[r.STATE_NAME][r.NAME] = {
			"noaa": {
				"males": r.MALES,
				"females": r.FEMALES,
				"families": r.FAMILIES,
				"asian": r.ASIAN,
				"black": r.BLACK,
				"hispanic": r.HISPANIC,
				"white": r.WHITE,
				"mult_race": r.MULT_RACE,
				"households": r.HOUSEHOLDS,
				"median_age": r.MED_AGE,
				"median_age_male": r.MED_AGE_M,
				"median_age_female": r.MED_AGE_F,
				"average_family_size": r.AVE_FAM_SZ,
			}
		}
		A.append(r.AVE_FAM_SZ)

	merger.merge(get_zips())
	merger.merge(get_demographics())
	merger.merge(get_cdc_deaths())
	merger.merge(get_labor_force())

	# Fatal police shootings are unique in that we don't have an
	# entry for every county, because the Washington Post tracks
	# stats by *shooting* rather than by county.  As a result, we
	# need to tolerate having missing counties.
	merger.merge(get_fatal_police_shootings(), allow_missing=True)
	# After we merge, add zeros for all missing counties (which
	# aren't present in the Washington Post dataset, simply because
	# they had no fatal police shootings).
	for state in merger.states:
		for county in merger.states[state]:
			if "fatal_police_shootings" not in merger.states[state][county]:
				merger.states[state][county]["fatal_police_shootings"] = {}
			for year in ['2018', '2019']:
				if f"total-{year}" not in merger.states[state][county]["fatal_police_shootings"]:
					merger.states[state][county]["fatal_police_shootings"][f"total-{year}"] = 0
				if f"unarmed-{year}" not in merger.states[state][county]["fatal_police_shootings"]:
					merger.states[state][county]["fatal_police_shootings"][f"unarmed-{year}"] = 0
				if f"firearmed-{year}" not in merger.states[state][county]["fatal_police_shootings"]:
					merger.states[state][county]["fatal_police_shootings"][f"firearmed-{year}"] = 0

	# We do the same thing for police deaths.
	merger.merge(get_police_deaths(), allow_missing=True)
	for state in merger.states:
		for county in merger.states[state]:
			if 'police_deaths' not in merger.states[state][county]:
				merger.states[state][county]['police_deaths'] = 0

	merger.merge(get_avg_income())
	merger.merge(get_covid())

	merger.merge(get_mobility(), allow_missing=True)

	# We're missing election data for Alaska and Kalawao County, HI
	merger.merge(get_elections(), missing={
		"Alaska": set(merger.states["Alaska"].keys()),
		"Hawaii": {"kalawao"}
	})

	with open('states.json', 'w+') as f:
		json.dump(merger.states, f, indent=2)

	with open('states.bson', 'wb+') as f:
		f.write(bson.dumps(merger.states))

