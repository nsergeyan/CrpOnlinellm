#pragma once
#include "PriorityHeuristic.h"

class RDH : public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	RDH(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
};

