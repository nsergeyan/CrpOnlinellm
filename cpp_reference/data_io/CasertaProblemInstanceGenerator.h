#pragma once
#include "ProblemInstanceGenerator.h"
#include <random>

class CasertaProblemInstanceGenerator :
    public ProblemInstanceGenerator
{
private:
	int numberOfStacks;
	int containersPerStack;
	std::default_random_engine rng;
	
public:
	CasertaProblemInstanceGenerator(int numberOfStacks, int containersPerStack);
	std::string GenerateInstance() override;
	std::string GenerateWeightsForInstance(int minimumWeight=1, int maximumWeight=30) override;
};

