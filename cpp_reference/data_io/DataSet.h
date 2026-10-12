#pragma once
#include "ProblemInstance.h"


class DataSet
{
protected:
	std::vector<ProblemInstance> problemInstances;
public:
	virtual void AddProblemInstance(ProblemInstance problemInstance);
	virtual const ProblemInstance& GetProblemInstance(int index);
	virtual int GetProblemInstanceNumber() const;
	virtual void GenerationPassed();
};


