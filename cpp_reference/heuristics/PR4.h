#pragma once
#include "PriorityHeuristic.h"
class PR4 :
    public PriorityHeuristic
{
private:
	double retrievalRate;
public:
	PR4(double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
	Location GetMove(ContainerYard& containerYard) override;
};

