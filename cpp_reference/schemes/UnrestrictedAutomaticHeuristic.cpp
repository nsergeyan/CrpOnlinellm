#include "UnrestrictedAutomaticHeuristic.h"
#include <iostream>
#include "SelectHighestContainerStrategy.h"

UnrestrictedAutomaticHeuristic::UnrestrictedAutomaticHeuristic(std::string expression, shared_ptr<ContainerSourceSelectionStrategy> selectionStrategy, double retrievalRate) : evaluator(terminals)
{
	this->evaluator.ParseExpression(expression);
	containerSelection = selectionStrategy;
	this->retrievalRate = retrievalRate;
}

void UnrestrictedAutomaticHeuristic::Solve(ContainerYard& containerYard)
{
	const int bays = containerYard.GetNumberOfBays();
	const int stacks = containerYard.GetNumberOfStacks();

	int countersToRetrieved = containerYard.GetNumberOfContainers() * retrievalRate;

	relocationsBlocking = 0;
	relocationsUnlocking = 0;
	relocationsFitting = 0;

	while (!containerYard.Empty() && containerYard.GetNumberOFRetrieved() < countersToRetrieved)
	{
		const int containerId = containerYard.GetNextContainerId();
		auto containerLocation = containerSelection->selectLocation(containerYard, containerId);

		while (containerYard.GetTopContainerId(containerLocation) != containerId)
		{
			double bestPriority = DBL_MAX;
			double executionTime = DBL_MAX;
			Location selectedLocation(-1, -1);

			//cout<<containerYard.GetCurrentYardString()<<endl;

			
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					if (!containerYard.HasMaximumHeight(location) && location != containerLocation)
					{
						terminals.CalculateTerminals(containerYard, containerYard.GetTopContainerId(containerLocation), containerLocation, location);
						evaluator.Reset();
						const double priority = evaluator.Execute();

						//const int selectedContainerHeight = containerYard.GetStackHeight(location);
						const Location& craneLocation = containerYard.GetCraneLocation();
						if (bestPriority > priority)
						{
							bestPriority = priority;
							selectedLocation = location;
							executionTime = containerYard.CalculateTime(craneLocation, selectedLocation);
						}
						else if (bestPriority == priority)
						{
							const double selectedContainerExecutionTime = containerYard.CalculateTime(craneLocation, selectedLocation);
							if (executionTime > selectedContainerExecutionTime)
							{
								bestPriority = priority;
								selectedLocation = location;
								executionTime = selectedContainerExecutionTime;
							}
						}
					}
				}
			}
			/*if(selectedLocation.GetBay()==-1)
			{
				auto locations = containerYard.GetContainerLocations(containerId);

				containerLocation = *std::next(locations.begin(),offset);
				offset++;
				continue;
			}*/

			while (1) {
				if (containerYard.GetStackHeight(selectedLocation) != 0 && containerYard.GetTopContainerId(selectedLocation) < containerYard.GetTopContainerId(containerLocation))
				{
					Location selectedLocationLow(-1, -1);
					int lowestIndex = INT_MAX;
					for (int bay = 0; bay < bays; bay++)
					{
						for (int stack = 0; stack < stacks; stack++)
						{
							Location location = Location(bay, stack);
							if (!containerYard.HasMaximumHeight(location) && location != containerLocation && location != selectedLocation)
							{
								int selectedStackLowestIndex = INT_MAX;
								for (int height = 0; height < containerYard.GetStackHeight(location); height++)
								{
									int currentContainerId = containerYard.GetContainerId(location, height);
									if (selectedStackLowestIndex > currentContainerId)
									{
										selectedStackLowestIndex = currentContainerId;
									}
								}
								if (selectedStackLowestIndex > containerYard.GetTopContainerId(selectedLocation))
								{
									if (lowestIndex > selectedStackLowestIndex)
									{
										lowestIndex = selectedStackLowestIndex;
										selectedLocationLow = location;
									}
									else if (selectedStackLowestIndex == INT_MAX)
									{
										lowestIndex = 0;
										selectedLocationLow = location;
									}
								}
							}


						}
					}
					if (selectedLocationLow != Location(-1, -1))
					{
						containerYard.Relocate(selectedLocation, selectedLocationLow);
						relocationsUnlocking++;
					} else
					{
						break;
					}
				}
				else
				{
					break;
				}
			}
			
			containerYard.Relocate(containerLocation, selectedLocation);
			relocationsBlocking++;
			//	std::cout << containerYard->GetCurrentYardString();
		}

		containerYard.Retrieve(containerLocation);
		//std::cout << containerYard->GetCurrentYardString();
	}
}


int UnrestrictedAutomaticHeuristic::GetRelocationsBlocking()
{
	return relocationsBlocking;
}

int UnrestrictedAutomaticHeuristic::GetRelocationsUnblocking()
{
	return relocationsUnlocking;
}

int UnrestrictedAutomaticHeuristic::GetRelocationsFitting()
{
	return relocationsFitting;
}

int UnrestrictedAutomaticHeuristic::getPrirotyFunctionCalls()
{
	return evaluator.GetCalls();
}
