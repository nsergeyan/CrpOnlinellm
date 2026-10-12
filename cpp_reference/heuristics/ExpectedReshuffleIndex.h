#pragma once
#include "PriorityHeuristic.h"

class ExpectedReshuffleIndex : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	ExpectedReshuffleIndex(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

