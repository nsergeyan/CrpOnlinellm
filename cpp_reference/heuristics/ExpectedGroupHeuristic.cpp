#include "ExpectedGroupHeuristic.h"

#include "ReshuffleIndex.h"
#include "SelectFirstAvailabelContainerStrategy.h"

ExpectedGroupHeuristic::ExpectedGroupHeuristic(double retrievalRate)
{
	this->retrievalRate = retrievalRate;
}

void ExpectedGroupHeuristic::Solve(ContainerYard& containerYard)
{
    int bays = containerYard.GetNumberOfBays();
    int stacks = containerYard.GetNumberOfStacks();
    ContainerSourceSelectionStrategy* containerSelection =
        new SelectFirstAvailabelContainerStrategy();

    while (!containerYard.Empty())
    {
        int targetContainerId = containerYard.GetNextContainerId();
        Location containerLocation =
            containerSelection->selectLocation(containerYard, targetContainerId);

        int countersToRetrieved =
            containerYard.GetNumberOfContainers() * retrievalRate;

        while (containerYard.GetTopContainerId(containerLocation) != targetContainerId &&
            containerYard.GetNumberOFRetrieved() < countersToRetrieved)
        {
            
            std::vector<int> blockingContainers;
            while (containerYard.GetTopContainerId(containerLocation) != targetContainerId)
            {
                blockingContainers.push_back(
                    containerYard.RemoveTopContainer(containerLocation));
            }

            for (int i = 0; i < blockingContainers.size(); i++)
            {
                int c = blockingContainers[i];

                int bestERI = INT_MAX;
                Location bestLocation(-1, -1);
                int bestMinS = INT_MAX;

                for (int bay = 0; bay < bays; bay++)
                {
                    for (int stack = 0; stack < stacks; stack++)
                    {
                        Location loc(bay, stack);
                        if (loc == containerLocation ||
                            containerYard.HasMaximumHeight(loc))
                            continue;
                        
                        int minLabel = INT_MAX;
                        int countERI = 0;
                        for (int h = 0; h < containerYard.GetStackHeight(loc); h++)
                        {
                            int topId = containerYard.GetContainerId(loc, h);
                            if (topId < c)
                                countERI++;       
                            if (topId < minLabel) minLabel = topId;
                        }

                        if (countERI < bestERI ||
                            (countERI == bestERI && minLabel > bestMinS))
                        {
                            bestERI = countERI;
                            bestLocation = loc;
                            bestMinS = minLabel;
                        }
                    }
                }

                containerYard.PutContainer(c, containerLocation);
                containerYard.Relocate(containerLocation, bestLocation);
            }
        }

        containerYard.Retrieve(containerLocation);
    }
}