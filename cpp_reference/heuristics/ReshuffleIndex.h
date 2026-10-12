#pragma once
#include "PriorityHeuristic.h"

class ReshuffleIndex : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	ReshuffleIndex(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

