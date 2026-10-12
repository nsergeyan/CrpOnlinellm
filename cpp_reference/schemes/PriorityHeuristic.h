#pragma once
#include "ContainerYard.h"

class PriorityHeuristic
{
public:
	virtual void Solve(ContainerYard& containerYard) = 0;
	virtual Location GetMove(ContainerYard& containerYard);
	virtual std::vector<double> GetPriorities(ContainerYard& containerYard);
};

