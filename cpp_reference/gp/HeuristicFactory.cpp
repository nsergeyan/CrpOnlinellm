#include "HeuristicFactory.h"
#include "CrpConstants.h"
#include <RestrictedAutomaticHeuristic.h>
#include "ParameterUtils.h"
#include <UnrestrictedAutomaticHeuristic.h>
#include <UnrestrictedAutomaticHeuristicAllCombinations.h>
#include <UnrestrictedAutomaticHeuristicWithPrelocationRule.h>
#include <RestrictedAutomaticHeuristicWithoutNextStack.h>
#include <UnrestrictedAutomaticTwoTreesHeuristic.h>
#include <RestrictedTwoTreesAutomaticHeuristic.h>
#include <UnrestrictedAutomaticHeuristicAllCombinationsTwoTrees.h>
//#include <RestrictedAutomaticDuplicateHeuristic.h>
//#include <UnrestrictedAutomaticDuplicateHeuristic.h>
#include <RestrictedGlobalRetrievalHeuristic.h>
#include <UnrestrictedGlobalRetrievalHeuristic.h>
#include <RestrictedGlobalRetrievalHeuristicParameters.h>
#include <UnrestrictedGlobalRetrievalHeuristicParameters.h>
#include <ContainerSelectionType.h>
#include <SelectFirstAvailabelContainerStrategy.h>
#include <ChainAutomaticHeuristic.h>
#include <RestrictedAutomaticPrelocationHeuristic.h>
#include <UnrestrictedAutomaticPrelocationHeuristic.h>
#include <RestrictedAutomaticWellPlaced.h>
#include "GlobalRetrievalHeuristicSettings.h"
#include "DynamicUnrestrictedAutomaticHeuristic.h"
#include "DynamicRestrictedAutomaticHeuristic.h"
#include "DynamicRestrictedAutomaticTwoRulesHeuristic.h"
#include "DynamicUnrestrictedAutomaticTwoRulesHeuristic.h"



std::unique_ptr<PriorityHeuristic> HeuristicFactory::CreateHeuristic(StateP state, IndividualP individual)
{
	string heuristicType = ParameterUtils::GetParameterValue<std::string>(state, HEURISTIC_TYPE_PARAMETER);


	std::unique_ptr<PriorityHeuristic> heuristic;

	if (dynamic_cast<Tree::Tree*>(individual->getGenotype().get()) != nullptr) {
		std::string expression = ParseTree(individual);

		auto containerSelectionStrategy = containerSelectionFactory.CreateSelectionStrategy(state);

		if (heuristicType == RESTRICTED_STANDARD_HEURISTIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		}
		else if (heuristicType == RESTRICTED_WITHOUT_NEXT_HEURISTIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticHeuristicWithoutNextStack(expression));
		}
		else if (heuristicType == RESTRICTED_TWO_TREES_HEURISTIC)
		{
			std::string expression2 = ParseTree(individual, 1);
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedTwoTreesAutomaticHeuristic(expression, expression2));
		}

		else if (heuristicType == UNRESTRICTED_AUTOMATIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		}
		else if (heuristicType == UNRESTRICTED_ALL_COMBINATIONS_HEURISTIC)
		{
			int numberOfRelocations = ParameterUtils::GetParameterValue<int>(state, RELOCATIONS_PARAMETER);
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticHeuristicAllCombinations(expression, numberOfRelocations));
		}
		else if (heuristicType == UNRESTRICTED_ALL_COMBINATIONS_TWO_TREES_HEURISTIC)
		{
			std::string expression2 = ParseTree(individual, 1);
			int numberOfRelocations = ParameterUtils::GetParameterValue<int>(state, RELOCATIONS_PARAMETER);
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticHeuristicAllCombinationsTwoTrees(expression, expression2, numberOfRelocations));
		}

		else if (heuristicType == UNRESTRICTED_WITH_PRELOCATION_RULES)
		{
			std::string expression2 = ParseTree(individual, 1);
			int numberOfRelocations = ParameterUtils::GetParameterValue<int>(state, RELOCATIONS_PARAMETER);
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticHeuristicWithPrelocationRule(expression, expression2, numberOfRelocations));
		}

		else if (heuristicType == UNRESTRICTED_AUTOMATIC_TWO_TREES)
		{
			std::string expression2 = ParseTree(individual, 1);

			//int numberOfRelocations = ParameterUtils::GetParameterValue<int>(state, RELOCATIONS_PARAMETER);
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticTwoTreesHeuristic(expression, expression2));
		}

		else if (heuristicType == RESTRICTED_STANDARD_DUPLICATE_HEURISTIC)
		{
			string selectionStrategyString = ParameterUtils::GetParameterValue<std::string>(state, CONTAINER_SELECTION_STRATEGY);
			ContainerSelectionType selectionType = selectionStrategyString == SELECT_FIRST_AVAILABLE ? SELECT_FIRST_AVAILABLE_STRATEGY : SELECT_HIGHEST_STRATEGY;
			std::string expression2 = ParseTree(individual, 1);
			//heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticDuplicateHeuristic(expression, expression2, selectionType));
		}

		else if (heuristicType == UNRESTRICTED_AUTOMATIC_DUPLICATE)
		{
			string selectionStrategyString = ParameterUtils::GetParameterValue<std::string>(state, CONTAINER_SELECTION_STRATEGY);
			ContainerSelectionType selectionType = selectionStrategyString == SELECT_FIRST_AVAILABLE ? SELECT_FIRST_AVAILABLE_STRATEGY : SELECT_HIGHEST_STRATEGY;
			std::string expression2 = ParseTree(individual, 1);
			//heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticDuplicateHeuristic(expression, expression2, selectionType));
		}
		else if(heuristicType == RESTRICTED_CHAIN)
		{
			int chainStrategy = ParameterUtils::GetParameterValue<int>(state, RESTRICTED_CHAIN_STRATEGY);
			heuristic = std::unique_ptr<PriorityHeuristic>(new ChainAutomaticHeuristic(expression, containerSelectionStrategy,chainStrategy));
		}
		else if (heuristicType == RESTRICTED_WELL_PLACED)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticWellPlaced(expression, containerSelectionStrategy));
		} else if(heuristicType == RESTRICTED_PRELOCATION)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticPrelocationHeuristic(expression, containerSelectionStrategy));
		} else if(heuristicType == UNRESTRICTED_PRELOCATION)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticPrelocationHeuristic(expression, containerSelectionStrategy));
		}
		else if(heuristicType == RESTRICTED_DYNAMIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new DynamicRestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		} else if(heuristicType == UNRESTRICTED_DYNAMIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new DynamicUnrestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		}
		else if (heuristicType == RESTRICTED_DYNAMIC_TWO_RULES)
		{
			string selectionStrategyString = ParameterUtils::GetParameterValue<std::string>(state, CONTAINER_SELECTION_STRATEGY);
			ContainerSelectionType selectionType = selectionStrategyString == SELECT_FIRST_AVAILABLE ? SELECT_FIRST_AVAILABLE_STRATEGY : SELECT_HIGHEST_STRATEGY;
			std::string expression2 = ParseTree(individual, 1);
			heuristic = std::unique_ptr<PriorityHeuristic>(new DynamicRestrictedAutomaticTwoRulesHeuristic(expression, expression2, containerSelectionStrategy));
		}
		else if (heuristicType == UNRESTRICTED_DYNAMIC_TWO_RULES)
		{
			string selectionStrategyString = ParameterUtils::GetParameterValue<std::string>(state, CONTAINER_SELECTION_STRATEGY);
			ContainerSelectionType selectionType = selectionStrategyString == SELECT_FIRST_AVAILABLE ? SELECT_FIRST_AVAILABLE_STRATEGY : SELECT_HIGHEST_STRATEGY;
			std::string expression2 = ParseTree(individual, 1);
			heuristic = std::unique_ptr<PriorityHeuristic>(new DynamicUnrestrictedAutomaticTwoRulesHeuristic(expression, expression2, containerSelectionStrategy));
		}
	}
	else {
		int gaParameters = ParameterUtils::GetParameterValue<int>(state, GA_PARAMETERS);

		std::shared_ptr<GlobalRetrievalHeuristicSettings> GRHS = readIndividual(individual);
		auto containerSelectionStrategy = containerSelectionFactory.CreateSelectionStrategy(state);

		if (gaParameters == 0) {

			if (heuristicType == RESTRICTED_STANDARD_HEURISTIC)
			{
				heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedGlobalRetrievalHeuristic(containerSelectionStrategy, GRHS));
			}
			else if (heuristicType == UNRESTRICTED_AUTOMATIC)
			{
				heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedGlobalRetrievalHeuristic(containerSelectionStrategy, GRHS));
			}
		}
		else if (gaParameters == 1) {
			if (heuristicType == RESTRICTED_STANDARD_HEURISTIC)
			{
				heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedGlobalRetrievalHeuristicParameters(containerSelectionStrategy, GRHS));
			}
			else if (heuristicType == UNRESTRICTED_AUTOMATIC)
			{
				heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedGlobalRetrievalHeuristicParameters(containerSelectionStrategy, GRHS));
			}
		}


	}
	
	return heuristic;
}

std::unique_ptr<PriorityHeuristic> HeuristicFactory::CreateHeuristic(std::string heuristicType, IndividualP individual)
{
	std::unique_ptr<PriorityHeuristic> heuristic;

	if (dynamic_cast<Tree::Tree*>(individual->getGenotype().get()) != nullptr) {
		std::string expression = ParseTree(individual);

		auto containerSelectionStrategy = std::shared_ptr<ContainerSourceSelectionStrategy>(new SelectFirstAvailabelContainerStrategy());

		if (heuristicType == RESTRICTED_STANDARD_HEURISTIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		}
		else if (heuristicType == UNRESTRICTED_AUTOMATIC)
		{
			heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedAutomaticHeuristic(expression, containerSelectionStrategy));
		}
	}
	return heuristic;
}

std::string HeuristicFactory::ParseTree(IndividualP individual, int treeIndex )
{
	Tree::Tree* tree = (Tree::Tree*)individual->getGenotype(treeIndex).get();

	std::stringstream sValue;
	for (uint i = 0; i < tree->size(); i++) {
		sValue << (*tree)[i]->primitive_->getName() << " ";
	}
	return sValue.str();
}


/*std::unique_ptr<PriorityHeuristic> HeuristicFactory::CreateHeuristicGA(StateP state, IndividualP individual)
{
	string heuristicType = ParameterUtils::GetParameterValue<std::string>(state, HEURISTIC_TYPE_PARAMETER);

	std::unique_ptr<PriorityHeuristic> heuristic;
	std::shared_ptr<GlobalRetrievalHeuristicSettings> GRHS = readIndividual(individual);
	
	auto containerSelectionStrategy = containerSelectionFactory.CreateSelectionStrategy(state);

	if (heuristicType == RESTRICTED_STANDARD_HEURISTIC)
	{
		heuristic = std::unique_ptr<PriorityHeuristic>(new RestrictedGlobalRetrievalHeuristic(containerSelectionStrategy, GRHS));
	}
	else if (heuristicType == UNRESTRICTED_AUTOMATIC)
	{
		heuristic = std::unique_ptr<PriorityHeuristic>(new UnrestrictedGlobalRetrievalHeuristic(containerSelectionStrategy, GRHS));
	}

	return heuristic;
}
*/

std::shared_ptr<GlobalRetrievalHeuristicSettings> HeuristicFactory::readIndividual(IndividualP individual) {
	FloatingPoint::FloatingPoint* gen = (FloatingPoint::FloatingPoint*)individual->getGenotype().get();

	vector<double> params;
	for (uint i = 0; i < gen->realValue.size(); i++)
		params.push_back(gen->realValue[i]);
	std::shared_ptr<GlobalRetrievalHeuristicSettings> GRHS = std::shared_ptr<GlobalRetrievalHeuristicSettings>(new GlobalRetrievalHeuristicSettings(params));
	
	return  GRHS;
}