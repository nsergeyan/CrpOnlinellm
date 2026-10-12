#include "CasertaProblemInstanceGenerator.h"
#include <vector>
#include  <algorithm>
#include <random>
#include <sstream>
#include <deque>
#include <ctime>
#include <chrono>

CasertaProblemInstanceGenerator::CasertaProblemInstanceGenerator(int numberOfStacks, int containersPerStack)
{
	this->numberOfStacks = numberOfStacks;
	this->containersPerStack = containersPerStack;
	srand(time(NULL));
}

std::string CasertaProblemInstanceGenerator::GenerateInstance()
{
	std::deque<int> containers;
	for(int i = 1; i<=numberOfStacks*containersPerStack; i++)
	{
		containers.push_back(i);
	}

	unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
	auto rng = std::default_random_engine{seed};
	std::shuffle(containers.begin(), containers.end(), rng);

	std::stringstream problemInstance;

	problemInstance << numberOfStacks << " " << numberOfStacks * containersPerStack << "\n";
	
	for(int stack=0; stack<numberOfStacks; stack++)
	{
		problemInstance << containersPerStack;
		for(int container = 0; container<containersPerStack; container++)
		{
			problemInstance << " " << containers.front();
			containers.pop_front();
		}
		problemInstance << "\n";
	}

	problemInstance << "\n";


	return problemInstance.str();
}

std::string CasertaProblemInstanceGenerator::GenerateWeightsForInstance(int minimumWeight, int maximumWeight)
{
	std::stringstream instanceWeights;

	std::random_device device;
	std::mt19937 rng(device());
	std::uniform_int_distribution<int> dist(minimumWeight, maximumWeight);

	for (int i = 1; i <= numberOfStacks * containersPerStack; i++)
	{
		instanceWeights << std::to_string(i) << " " << dist(rng) << "\n";
	}
	return instanceWeights.str();
	
}
