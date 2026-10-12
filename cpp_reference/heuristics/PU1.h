#pragma once
#include "PriorityHeuristic.h"

class PU1 :
	public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	PU1(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;

};

