#pragma once
#include "ContainerYard.h"
#include "PriorityHeuristic.h"

class ExpectedGroupHeuristic : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	ExpectedGroupHeuristic(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

