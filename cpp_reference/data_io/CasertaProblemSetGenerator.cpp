#include "CasertaProblemSetGenerator.h"

#include <filesystem>

#include "CasertaProblemInstanceGenerator.h"
#include <vector>
#include <sstream>
#include <fstream>

void CasertaProblemSetGenerator::Generate(std::string outputLocation)
{
	//std::vector<std::vector<int>> stacks = { { 3,4,5,6,7,8 },
	//					 { 4, 5, 6, 7 },
	//					 { 4, 5, 6, 7, 8, 9, 10 },
	//					 
	//	{6,10},{6,10} };

	//std::vector<int> containersPerStacks = { 3,4,5,6,10 };

	std::vector<std::vector<int>> stacks = { {10} };

	std::vector<int> containersPerStacks = { 10 };

	int instancesPerParameter = 3000;
	
	int counter = 0;
			for (auto containersPerStack : containersPerStacks)
			{
				for (auto stack : stacks[counter]) {
					CasertaProblemInstanceGenerator generator(stack, containersPerStack);
					for (int instance = 0; instance < instancesPerParameter; instance++)
					{
						std::string	instanceString = generator.GenerateInstance();
						std::stringstream fileName;
						fileName << outputLocation << "\\data" << containersPerStack << "-" << stack << "-" << instance << ".dat";
						std::ofstream out(fileName.str());
						out << instanceString;
						out.close();
					}
				}
				counter++;
			}
			
	}


void CasertaProblemSetGenerator::GenerateInstanceWeights(std::string outputLocation)
{
	std::vector<std::vector<int>> stacks = { { 3,4,5,6,7,8 },
						 { 4, 5, 6, 7 },
						 { 4, 5, 6, 7, 8, 9, 10 },

		{6,10},{6,10} };

	std::vector<int> containersPerStacks = { 3,4,5,6,10 };

	int instancesPerParameter = 40;

	int counter = 0;
	std::filesystem::create_directories(outputLocation + "\\weights");
	for (auto containersPerStack : containersPerStacks)
	{
		for (auto stack : stacks[counter]) {
			CasertaProblemInstanceGenerator generator(stack, containersPerStack);
			for (int instance = 0; instance < instancesPerParameter; instance++)
			{
				std::string	instanceString = generator.GenerateWeightsForInstance();
				std::stringstream fileName;
				fileName << outputLocation << "\\" << "weights" << "\\" << "data" << containersPerStack << "-" << stack << "-" << instance << ".dat";
				std::ofstream out(fileName.str());
				out << instanceString;
				out.close();
			}
		}
		counter++;
	}
}
