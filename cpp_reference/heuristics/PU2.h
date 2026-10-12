#pragma once
#include "PriorityHeuristic.h"

class PU2:
	public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	PU2(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

