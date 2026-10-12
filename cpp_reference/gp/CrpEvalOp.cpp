#include "CrpEvalOp.h"
#include <RestrictedAutomaticHeuristic.h>
#include <SequentialSubDataSet.h>
#include <RandomSubDataSet.h>
#include <StringUtils.h>

#include "CrpConstants.h"
#include "DataSetFactory.h"
#include "ParameterUtils.h"
#include "IndividualUtils.h"

void CrpEvalOp::registerParameters(StateP state)
{
	// Name of directory containing all instances
	state->getRegistry()->registerEntry(TRAIN_SET_PARAMETER, (voidP)(new std::string("projects")), ECF::STRING);
	state->getRegistry()->registerEntry(TEST_SET_PARAMETER, (voidP)(new std::string("clean")), ECF::STRING);
	state->getRegistry()->registerEntry(VALIDATION_SET_PARAMETER, (voidP)(new std::string("validation")), ECF::STRING);

	state->getRegistry()->registerEntry(SUBSET_TYPE_PARAMETER, (voidP)(new std::string("none")), ECF::STRING);
	state->getRegistry()->registerEntry(SUBSET_SIZE_PARAMETER, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_SHUFFLE_ON_START, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_SHUFFLE, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_SEQUENTIAL, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_GROW, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_SHUFFLE_INTERVAL, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_SEQUENTIAL_INTERVAL, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_GROW_INTERVAL, (voidP)(new int(1)), ECF::INT);
	state->getRegistry()->registerEntry(SUBSET_GROW_RATIO, (voidP)(new double(1)), ECF::DOUBLE);

	state->getRegistry()->registerEntry(DATASET_TYPE_PARAMETER, (voidP)(new std::string("caserta")), ECF::STRING);
	state->getRegistry()->registerEntry(CRITERION_PARAMETER, (voidP)(new std::string(RELOCATIONS_CRITERION)), ECF::STRING);
	state->getRegistry()->registerEntry(HEURISTIC_TYPE_PARAMETER, (voidP)(new std::string(RESTRICTED_STANDARD_HEURISTIC)), ECF::STRING);
	state->getRegistry()->registerEntry(RELOCATIONS_PARAMETER, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(CONTAINER_SELECTION_STRATEGY, (voidP)(new std::string(SELECT_FIRST_AVAILABLE)), ECF::STRING);
	state->getRegistry()->registerEntry(PROBLEM_UNCERTAINTY, (voidP)(new double(1.0)), ECF::DOUBLE);

	state->getRegistry()->registerEntry(USE_CONTAINER_GROUPS, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(CONTAINER_GROUP_SIZE_PARAMETER, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(CONTAINER_GROUP_COUNT_PARAMETER, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(IDS_KNOWN_IN_GROUP, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(GROUP_PARAMETER_TYPE, (voidP)(new string(CONTAINER_GROUP_COUNT)), ECF::STRING);

	state->getRegistry()->registerEntry(RESTRICTED_CHAIN_STRATEGY, (voidP)(new int(0)), ECF::INT);

	state->getRegistry()->registerEntry(USE_SURROGATE, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(SURROGATE_STRATEGY, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SHUFFLE_STRATEGY, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SURROGATE_SIZE, (voidP)(new int(0)), ECF::INT);

	state->getRegistry()->registerEntry(SURROGATE_STRATEGY, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SURROGATE_STRATEGY, (voidP)(new string("")), ECF::STRING);


	state->getRegistry()->registerEntry(USE_SIMILARITY_SURROGATE, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(SURROGATE_NEIGHBOUR_COUNT, (voidP)(new int(0)), ECF::INT);
	state->getRegistry()->registerEntry(SURROGATE_DECISION_FILE, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SURROGATE_FITNESS_FILE, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SURROGATE_SELECTED_SCENARIOS_FILE, (voidP)(new string("")), ECF::STRING);
	state->getRegistry()->registerEntry(SURROGATE_DATASET_PATH, (voidP)(new string("")), ECF::STRING);

}

CrpEvalOp::CrpEvalOp(std::shared_ptr<EvaluationUtils> utils, int port) : server(port), client("127.0.0.1", port)
{
	this->utils = utils;
	//if (!server.start()) return;       // do initialisation here
	//if (!server.waitForClient()) return;
	//client.connectToServer();

}

bool CrpEvalOp::initialize(StateP state)
{
	state_ = state;
	// Read params
	criterion = ParameterUtils::GetParameterValue<std::string>(state, CRITERION_PARAMETER);
	
	DataSetFactory dsFactory;
	ds = utils->trainSet;
	surrogate = utils->surrogateModel;

	auto decisions = ParameterUtils::GetParameterValue<std::string>(state, SURROGATE_DECISION_FILE);
	auto fitnessValues= ParameterUtils::GetParameterValue<std::string>(state, SURROGATE_FITNESS_FILE);
	auto scenarios= ParameterUtils::GetParameterValue<std::string>(state, SURROGATE_SELECTED_SCENARIOS_FILE);
	auto dataset = ParameterUtils::GetParameterValue<std::string>(state, SURROGATE_DATASET_PATH);
	auto neighbours = ParameterUtils::GetParameterValue<int>(state, SURROGATE_NEIGHBOUR_COUNT);


	//approximateionSurrogate.Initialise(dataset, decisions, fitnessValues,scenarios, neighbours);
	return true;
}

FitnessP CrpEvalOp::evaluate(IndividualP individual)
{
	FitnessP fitness = static_cast<FitnessP> (new FitnessMin);

	//auto heap = IndividualUtils::prefixToHeap(factory.ParseTree(individual), 5);

	//client.sendMessage(heap);

	//float result;
	//client.receiveFloat(result);
	////cout << result << endl;
	//fitness->setValue(result);
	//return fitness;

	double totalSolution = 0;
	double totalTime = 0;
	double totalEnergy = 0;

	auto heuristic = factory.CreateHeuristic(state_, individual);

	double uncertainty = ParameterUtils::GetParameterValue<double>(state_, PROBLEM_UNCERTAINTY);

	
	int numberOfGroups = 0;
	int groupSize = 0;
	bool useGroups = false;
	bool idsKnownWithinGroup = false;
	bool useGroupSize = false;

	bool useContainerGroups = ParameterUtils::GetParameterValue<int>(state_, USE_CONTAINER_GROUPS) == 0 ? false : true;

	if(useContainerGroups)
	{
		useGroups = true;
		idsKnownWithinGroup = ParameterUtils::GetParameterValue<int>(state_, IDS_KNOWN_IN_GROUP) == 0 ? false : true;
		std::string parameterType = ParameterUtils::GetParameterValue<string>(state_, GROUP_PARAMETER_TYPE);
		if( parameterType == CONTAINER_GROUP_SIZE)
		{
			useGroupSize = true;
			groupSize = ParameterUtils::GetParameterValue<int>(state_, CONTAINER_GROUP_SIZE_PARAMETER);
		} else
		{
			numberOfGroups = ParameterUtils::GetParameterValue<int>(state_, CONTAINER_GROUP_COUNT_PARAMETER);
		}
	}
	vector<int> fitness_values;

	for (int i = 0; i < ds->GetProblemInstanceNumber(); i++)
	{


		auto problemInstance = ds->GetProblemInstance(i);

		if(useGroupSize)
		{
			numberOfGroups = problemInstance.GetNumberOfContainers() / groupSize;
		}

		auto yard = problemInstance.CreateContainerYard(3.5, 1.2, 40, 30,-1, uncertainty, numberOfGroups, useGroups, idsKnownWithinGroup);
		
		heuristic->Solve(yard);
		auto solution = yard.GetSolution();
		totalSolution += solution.GetNumberOfMoves();
		totalTime += solution.GetTotalExecutionTime();
		totalEnergy += solution.GetTotalEnergyConsumption();

		fitness_values.push_back(solution.GetNumberOfMoves());

	}
	if(criterion==RELOCATIONS_CRITERION)
	{
		fitness->setValue(totalSolution);
	} else if(criterion == TIME_CRITERION)
	{
		fitness->setValue(totalTime);
	} else if(criterion == ENERGY_CRITERION)
	{
		fitness->setValue(totalEnergy);
	}
	else if(criterion == REL_TIME)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);
		
		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == REL_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == TIME_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == REL_TIME_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	auto parsed = factory.ParseTree(individual);

	if(fitnessValues.find(parsed)==fitnessValues.end())
	{
		ordered_individuals.push_back(parsed);
		fitnessValues[parsed] = fitness_values;

	}

	return fitness;
}



FitnessP CrpEvalOp::evaluateSurrogate(IndividualP individual)
{

	FitnessP fitness = static_cast<FitnessP> (new FitnessMin);

	//auto heap = IndividualUtils::prefixToHeap(factory.ParseTree(individual), 5);
	//client.sendMessage(heap);

	//float result;
	//client.receiveFloat(result);
	////cout << result << endl;
	//fitness->setValue(result);
	//return fitness;

	//auto fitnessValue = approximateionSurrogate.PredictFitness(individual);

	//fitness->setValue(fitnessValue);
	//return fitness;



	double totalSolution = 0;
	double totalTime = 0;
	double totalEnergy = 0;

	auto heuristic = factory.CreateHeuristic(state_, individual);

	double uncertainty = ParameterUtils::GetParameterValue<double>(state_, PROBLEM_UNCERTAINTY);


	int numberOfGroups = 0;
	int groupSize = 0;
	bool useGroups = false;
	bool idsKnownWithinGroup = false;
	bool useGroupSize = false;

	bool useContainerGroups = ParameterUtils::GetParameterValue<int>(state_, USE_CONTAINER_GROUPS) == 0 ? false : true;

	if (useContainerGroups)
	{
		useGroups = true;
		idsKnownWithinGroup = ParameterUtils::GetParameterValue<int>(state_, IDS_KNOWN_IN_GROUP) == 0 ? false : true;
		std::string parameterType = ParameterUtils::GetParameterValue<string>(state_, GROUP_PARAMETER_TYPE);
		if (parameterType == CONTAINER_GROUP_SIZE)
		{
			useGroupSize = true;
			groupSize = ParameterUtils::GetParameterValue<int>(state_, CONTAINER_GROUP_SIZE_PARAMETER);
		}
		else
		{
			numberOfGroups = ParameterUtils::GetParameterValue<int>(state_, CONTAINER_GROUP_COUNT_PARAMETER);
		}
	}


	for (int i = 0; i < surrogate->GetProblemInstanceNumber(); i++)
	{


		auto problemInstance = surrogate->GetProblemInstance(i);

		if (useGroupSize)
		{
			numberOfGroups = problemInstance.GetNumberOfContainers() / groupSize;
		}

		auto yard = problemInstance.CreateContainerYard(3.5, 1.2, 40, 30, -1, uncertainty, numberOfGroups, useGroups, idsKnownWithinGroup);

		heuristic->Solve(yard);
		auto solution = yard.GetSolution();
		totalSolution += solution.GetNumberOfMoves();
		totalTime += solution.GetTotalExecutionTime();
		totalEnergy += solution.GetTotalEnergyConsumption();
	}
	if (criterion == RELOCATIONS_CRITERION)
	{
		fitness->setValue(totalSolution);
	}
	else if (criterion == TIME_CRITERION)
	{
		fitness->setValue(totalTime);
	}
	else if (criterion == ENERGY_CRITERION)
	{
		fitness->setValue(totalEnergy);
	}
	else if (criterion == REL_TIME)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);

		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == REL_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == TIME_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	else if (criterion == REL_TIME_ENE)
	{
		MOFitnessP fitness = static_cast<MOFitnessP> (new MOFitness);
		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalSolution);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalTime);

		fitness->push_back((FitnessP) new FitnessMin);
		fitness->back()->setValue(totalEnergy);

		return static_cast<FitnessP> (fitness);
	}

	return fitness;
}

void CrpEvalOp::changeDataSet()
{

	ds->GenerationPassed();
	/*if (SequentialSubDataSet* sds = dynamic_cast<SequentialSubDataSet*>(ds.get()))
	{
		sds->SetNextBatch();
	}
	if (RandomSubDataSet* sds = dynamic_cast<RandomSubDataSet*>(ds.get()))
	{
		sds->SetNextBatch();
	}*/
}

void CrpEvalOp::generationPassed()
{

	ds->GenerationPassed();
	/*if (SequentialSubDataSet* sds = dynamic_cast<SequentialSubDataSet*>(ds.get()))
	{
		sds->SetNextBatch();
	}
	if (RandomSubDataSet* sds = dynamic_cast<RandomSubDataSet*>(ds.get()))
	{
		sds->SetNextBatch();
	}*/
}

void CrpEvalOp::resizeDataSetToMaximumSize()
{
	if (SequentialSubDataSet* sds = dynamic_cast<SequentialSubDataSet*>(ds.get()))
	{
		sds->UpdateSubsetSize(sds->GetEntireProblemInstanceSize());
	}
	if (RandomSubDataSet* sds = dynamic_cast<RandomSubDataSet*>(ds.get()))
	{
		sds->UpdateSubsetSize(sds->GetEntireProblemInstanceSize());
	}
}
 