from typing import Any, Dict, Optional, Tuple

from ..nrw_model.policies import NRWMitigation
from ..sources.interventions import OpenSource, CloseSource
from ..pumping_stations.interventions import InstallPumps
from ..connections.interventions import InstallPipe
from ..energy.interventions import InstallSolarFarm
from ..water_utilities.policies import WaterPricingAdjustment, BondRatioAdjustment
from ..national_context.policies import BudgetAllocation

NationalPolicies = [BudgetAllocation]
NationalInterventions = [InstallPipe]
WaterUtilityPolicies = [
	NRWMitigation,
	WaterPricingAdjustment,
	BondRatioAdjustment
]
WaterUtilityInterventions = [
	OpenSource,
	CloseSource,
	InstallPumps,
	InstallPipe,
	InstallSolarFarm
]

class Masterplan:
	def __init__(self, data: Dict[str, Any]):
		"""
		Initialize the Masterplan with a dictionary parsed from the YAML file.
		The structure is expected to have a 'years' key with a list of year dicts.
		Also index water utilities by year and water_utility id for fast access.
		"""
		self.__national_policies: Dict[int, Any] = {}
		self.__national_interventions: Dict[int, Any] = {}

		self.__wutilities_policies: Dict[Tuple[int, str], Any] = {}
		self.__wutilities_interventions: Dict[Tuple[int, str], Any] = {}

		for year_entry in data.get('years', []):
			year = year_entry['year']

			if 'national_policies' in year_entry:
				self.__national_policies[year] = year_entry['national_policies']
			if 'national_interventions' in year_entry:
				self.__national_interventions[year] = year_entry['national_interventions']

			for utility_entry in year_entry.get('water_utilities', []):
				wu = utility_entry['water_utility']
				
				if 'policies' in utility_entry:
					self.__wutilities_policies[(year, wu)] = utility_entry['policies']
				if 'interventions' in utility_entry:
					self.__wutilities_interventions[(year, wu)] = utility_entry['interventions']
    
	def policies(self, year: int, water_utility: Optional[str] = None) -> Optional[Dict[str, Any]]:
		"""
		Return the policy for a given year and optionally a specific water water_utility.
		If water_utility is None, return national_policies for the year.
		If water_utility is provided, return the policies for that water_utility in that year.
		"""
		if water_utility is None:
			return self.national_policies(year=year)
		
		return self.water_utility_policies(water_utility=water_utility, year=year)
	
	def interventions(self, year: int, water_utility: Optional[str] = None) -> Optional[Dict[str, Any]]:
		"""
		Return the interventions for a given year and optionally a specific water water_utility.
		If water_utility is None, return national_interventions for the year.
		If water_utility is provided, return the interventions for that water_utility in that year.
		"""
		if water_utility is None:
			return self.national_interventions(year=year)
		
		return self.water_utility_interventions(water_utility=water_utility, year=year)
	

	def national_policies(self, year: int) -> Dict[str, Any]:
		"""
		Return a dict of national policies for the given year, where each policy is the most recent value up to that year.
		"""
		policies = {}

		for policy_name in [np.NAME for np in NationalPolicies]:
			# Find the most recent year <= year with this policy
			most_recent = None
			for y in sorted(self.__national_policies.keys(), reverse=True):
				if y > year:
					continue
				policy_dict = self.__national_policies.get(y, {})
				if policy_name in policy_dict:
					most_recent = policy_dict[policy_name]
					break
			if most_recent is not None:
				policies[policy_name] = most_recent

		return policies

	def water_utility_policies(self, water_utility: str, year: int) -> Dict[str, Any]:
			"""
			Return a dict of policies for the given water utility and year, where each policy is the most recent value up to that year for that utility.
			"""
			policies = {}

			for policy_name in [wup.NAME for wup in WaterUtilityPolicies]:
				most_recent = None
				for y, wu in sorted(self.__wutilities_policies.keys(), reverse=True):
					if wu != water_utility or y > year:
						continue
					policy_dict = self.__wutilities_policies.get((y, wu), {})
					if policy_name in policy_dict:
						most_recent = policy_dict[policy_name]
						break
				if most_recent is not None:
					policies[policy_name] = most_recent

			return policies

	def national_interventions(self, year: int) -> Dict[str, Any]:
		"""
		Return a dict of national interventions for the given year, where each intervention is the most recent value up to that year.
		"""
		empty_interventions_year = {intv.NAME: [] for intv in NationalInterventions}

		actual_interventions_year = self.__national_interventions.get(year, {})

		return {**empty_interventions_year, **actual_interventions_year}

	def water_utility_interventions(self, water_utility: str, year: int) -> Dict[str, Any]:
		"""
		Return a dict of interventions for the given water utility and year, where each intervention is the most recent value up to that year for that utility.
		"""
		empty_interventions_year = {intv.NAME: [] for intv in WaterUtilityInterventions}

		actual_interventions_year = self.__wutilities_interventions.get((year, water_utility), {})

		return {**empty_interventions_year, **actual_interventions_year}