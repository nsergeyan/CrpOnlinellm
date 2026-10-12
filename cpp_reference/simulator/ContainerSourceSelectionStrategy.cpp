#include "ContainerSourceSelectionStrategy.h"

Location ContainerSourceSelectionStrategy::getSingleSourceLocation(ContainerYard& yard, int containerId)
{
	return yard.GetContainerLocation(containerId);
}
