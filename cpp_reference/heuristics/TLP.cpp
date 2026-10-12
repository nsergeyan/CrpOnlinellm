#include "TLP.h"
#include <iostream>
#include "SelectHighestContainerStrategy.h"
#include "SelectHighestContainerAlwaysStrategy.h"
#include "SelectMostContainersStrategy.h"
#include "SelectFirstAvailabelContainerStrategy.h"

TLP::TLP(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void TLP::Solve(ContainerYard& containerYard)
{
	int bays = containerYard.GetNumberOfBays();
	int stacks = containerYard.GetNumberOfStacks();

	ContainerSourceSelectionStrategy* containerSelection = new SelectFirstAvailabelContainerStrategy();

	int countersToRetrieved = containerYard.GetNumberOfContainers()*retrievalRate;


	while(!containerYard.Empty() && containerYard.GetNumberOFRetrieved()<countersToRetrieved)
	{
		int containerId = containerYard.GetNextContainerId();
		Location containerLocation(0,0);
		containerLocation = containerSelection->selectLocation(containerYard, containerId);

		while(containerYard.GetTopContainerId(containerLocation)!=containerId)
		{
			int stackHeight = INT_MAX;
			double executionTime = DBL_MAX;
			Location selectedLocation(-1, -1);
			for (int bay = 0; bay < bays; bay++)
			{
				for (int stack = 0; stack < stacks; stack++)
				{
					Location location = Location(bay, stack);

					
					if (location != containerLocation)
					{
						const int selectedContainerHeight = containerYard.GetStackHeight(location);
						Location craneLocation = containerYard.GetCraneLocation();
						if (stackHeight > selectedContainerHeight)
						{
							stackHeight = selectedContainerHeight;
							selectedLocation = location;
							executionTime = containerYard.CalculateTime(craneLocation, selectedLocation);
						}
						/*else if (stackHeight == selectedContainerHeight)
						{
							const double selectedContainerExecutionTime = containerYard.CalculateTime(craneLocation, location);
							if (executionTime > selectedContainerExecutionTime)
							{
								stackHeight = selectedContainerHeight;
								selectedLocation = location;
								executionTime = selectedContainerExecutionTime;
							}
						}*/
					}
				}
			}
			
			
			containerYard.Relocate(containerLocation, selectedLocation);
		//	std::cout << containerYard->GetCurrentYardString();
		}

		containerYard.Retrieve(containerLocation);
		//std::cout << containerYard->GetCurrentYardString();

	}
}
