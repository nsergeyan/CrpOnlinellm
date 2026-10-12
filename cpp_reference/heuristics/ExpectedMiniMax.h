#pragma once
#include "ContainerYard.h"
#include "PriorityHeuristic.h"


class ExpectedMinMax : public PriorityHeuristic
{
private:
	double retrievalRate;
public: 
	ExpectedMinMax(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

