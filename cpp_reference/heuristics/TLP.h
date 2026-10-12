#pragma once
#include "PriorityHeuristic.h"

/// <summary>
/// Simple heuristic which allocates the container to the stack with the lowest height,
/// </summary>
class TLP : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	TLP(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

