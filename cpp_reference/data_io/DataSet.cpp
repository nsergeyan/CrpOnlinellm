#include "DataSet.h"

void DataSet::AddProblemInstance(ProblemInstance problemInstance)
{
	problemInstances.push_back(problemInstance);
}

const ProblemInstance& DataSet::GetProblemInstance(int index)
{
	return problemInstances[index];
}

int DataSet::GetProblemInstanceNumber() const
{
	return  problemInstances.size();
}

void DataSet::GenerationPassed()
{
}
