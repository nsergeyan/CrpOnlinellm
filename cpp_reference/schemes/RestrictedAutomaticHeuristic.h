#pragma once
#include "PriorityHeuristic.h"
#include "Evaluator.h"
#include "ContainerSourceSelectionStrategy.h"

class RestrictedAutomaticHeuristic :
    public PriorityHeuristic
{
private:
	Evaluator evaluator;
	Terminals terminals;
	shared_ptr<ContainerSourceSelectionStrategy> containerSelection;
	double retrievalRate;

public:
	RestrictedAutomaticHeuristic(std::string expression, shared_ptr<ContainerSourceSelectionStrategy> selectionStrategy, double retrievalRate = 1.0);
	void Solve(ContainerYard& containerYard) override;
	vector<double> GetPriorities(ContainerYard& containerYard) override;
	int getPrirotyFunctionCalls();
};

