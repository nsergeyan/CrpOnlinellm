#pragma once
#include "PriorityHeuristic.h"

/// <summary>
/// Equal to PR2 in Zhu
/// </summary>
class MinMax : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	MinMax(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};
