#include "Terminals.h"

Terminals::Terminals()
{
	allowedTerminals = { "SH", "DUR", "RI", "MIN", "DIS", "EMP", "AVG", "REM", "NEXT", "BLKD", "DIFF", "EMPTY", "GOOD", "WL", "NL", "CUR", "DSM", "NRC", "NCURR", "NSC", "HC", "DIFFIND", "CHAIN", "HCHAIN", "HS","LS","RS","GS","KS", "ENGY", "WGHT", "NUNC", "NPER", "NRAT", "NGRP", "GRPS"};
	initialiseTerminals();
}
 

void Terminals::initialiseTerminals()
{
	terminals.push_back(Terminal(SH, "SH", false));
	terminals.push_back(Terminal(DUR, "DUR", false));
	terminals.push_back(Terminal(RI, "RI", false));
	terminals.push_back(Terminal(MIN, "MIN", false));
	terminals.push_back(Terminal(DIS, "DIS", false));
	terminals.push_back(Terminal(EMP, "EMP", false));
	terminals.push_back(Terminal(AVG, "AVG", false));
	terminals.push_back(Terminal(REM, "REM", false));
	terminals.push_back(Terminal(NEXT, "NEXT", false));
	terminals.push_back(Terminal(BLKD, "BLKD", false));
	terminals.push_back(Terminal(DIFF, "DIFF", false));
	terminals.push_back(Terminal(EMPTY, "EMPTY", false));
	terminals.push_back(Terminal(WL, "WL", false));
	terminals.push_back(Terminal(NL, "NL", false));
	terminals.push_back(Terminal(CUR, "CUR", false));
	terminals.push_back(Terminal(DSM, "DSM", false));
	terminals.push_back(Terminal(NRC, "NRC", false));
	terminals.push_back(Terminal(NCURR, "NCURR", false));
	terminals.push_back(Terminal(NSC, "NSC", false));
	terminals.push_back(Terminal(HC, "HC", false));
	terminals.push_back(Terminal(DIFFIND, "DIFFIND", false));
	terminals.push_back(Terminal(CHAIN, "CHAIN", false));
	terminals.push_back(Terminal(HCHAIN, "HCHAIN", false));
	terminals.push_back(Terminal(HS, "HS", false));
	terminals.push_back(Terminal(LS, "LS", false));
	terminals.push_back(Terminal(RS, "RS", false));
	terminals.push_back(Terminal(GS, "GS", false));
	terminals.push_back(Terminal(KS, "KS", false));
	terminals.push_back(Terminal(ENGY, "ENGY", false));
	terminals.push_back(Terminal(WGHT, "WGHT", false));
	terminals.push_back(Terminal(NUNC, "NUNC", false));
	terminals.push_back(Terminal(NPER, "NPER", false));
	terminals.push_back(Terminal(NRAT, "NRAT", false));
	terminals.push_back(Terminal(NGRP, "NGRP", false));
	terminals.push_back(Terminal(GRPS, "GRPS", false));

	terminalValues.resize(terminals.size());
}

int Terminals::GetTerminalId(const string& terminalString)
{
	for(auto & terminal : terminals)
	{
		if(terminal.GetName() == terminalString)
		{
			terminal.SetActive(true);
			return  terminal.GetId();
		}
	}
	/*
	auto activeTerminal = activeTerminals.find(terminal);
	if(activeTerminal==activeTerminals.end())
	{
		int terminalId = activeTerminals.size();
		activeTerminals.insert(make_pair(terminal, terminalId));
		return terminalId;
	}
	return activeTerminal->second;*/
}

void Terminals::CalculateTerminals(ContainerYard& containerYard, int containerId, Location& source, Location& location)
{
	if(terminals[SH].IsActive())
	{
		terminalValues[terminals[SH].GetId()] = containerYard.GetStackHeight(location);
	}
	if(terminals[DUR].IsActive())
	{
		terminalValues[terminals[DUR].GetId()] = containerYard.CalculateTime(source, location);
	}
	if (terminals[RI].IsActive())
	{
		terminalValues[terminals[RI].GetId()] = containerYard.reshuffleIndex(location, containerId);
	}
	if (terminals[MIN].IsActive()) {
		terminalValues[terminals[MIN].GetId()] = containerYard.GetMinimumStack(location);
	}
	if(terminals[DIS].IsActive())
	{
		terminalValues[terminals[DIS].GetId()] = containerYard.CalculateDistance(source, location);
	}
	if(terminals[EMP].IsActive())
	{
		terminalValues[terminals[EMP].GetId()] = containerYard.GetMaxStackHeight() - containerYard.GetStackHeight(location);
	}
	if(terminals[AVG].IsActive())
	{
		terminalValues[terminals[AVG].GetId()] = containerYard.calculateAverageContainerID(location);
	}
	if(terminals[REM].IsActive())
	{
		terminalValues[terminals[REM].GetId()] = containerYard.ContainersAbove(location);
	}
	if(terminals[NEXT].IsActive())
	{
		if(containerYard.GetStackHeight(location)>1)
		{
			terminalValues[terminals[NEXT].GetId()] = containerYard.GetContainerId(location, containerYard.GetStackHeight(location) - 1);
		} else
		{
			terminalValues[terminals[NEXT].GetId()] = 0;
		}
	}
	
	if (terminals[BLKD].IsActive())
	{
		terminalValues[terminals[BLKD].GetId()] = containerYard.GetNumberOfBlocked(location, containerId);
	}

	if (terminals[DIFF].IsActive())
	{
		terminalValues[terminals[DIFF].GetId()] = containerYard.GetMinimumStack(location) - containerId;
	}

	if (terminals[EMPTY].IsActive())
	{
		if (containerYard.GetStackHeight(location) == 0)
			terminalValues[terminals[EMPTY].GetId()] = 1;
		else
			terminalValues[terminals[EMPTY].GetId()] = 0;
	}

	if (terminals[WL].IsActive())
	{
		terminalValues[terminals[WL].GetId()] = containerYard.GetWellLocatedCount(location);
	}

	if (terminals[NL].IsActive())
	{
		terminalValues[terminals[NL].GetId()] = containerYard.GetBadLocatedCount(location);
	}
	if (terminals[CUR].IsActive())
	{
		terminalValues[terminals[CUR].GetId()] = containerId;
	}
	if (terminals[DSM].IsActive())
	{

		terminalValues[terminals[DSM].GetId()] = containerYard.GetHeightofLowerIndex(location, containerId);
	}
	if(terminals[NRC].IsActive())
	{
		terminalValues[terminals[NRC].GetId()] = containerYard.GetRemainingNumberOfContainersOfId(containerYard.GetNextContainerId());
	}
	if(terminals[NCURR].IsActive())
	{

		terminalValues[terminals[NCURR].GetId()] = containerYard.GetNumberOfCurrentContainers(location);
	}
	if (terminals[NSC].IsActive())
	{
		if(containerYard.HasDuplicates())
		{
			terminalValues[terminals[NSC].GetId()] = containerYard.GetContainerLocations(containerId).size();
		} else
		{
			terminalValues[terminals[NSC].GetId()] = 1;
		}
	}
	if (terminals[HC].IsActive())
	{
		terminalValues[terminals[HC].GetId()] = containerYard.GetStackHeight(location)-containerYard.GetHeightOfCurrent(location);
	}
	if (terminals[DIFFIND].IsActive())
	{

		terminalValues[terminals[DIFFIND].GetId()] = containerYard.GetNumberOfDifferentIndices(location);
	}
	if (terminals[CHAIN].IsActive())
	{

		terminalValues[terminals[CHAIN].GetId()] = containerYard.GetChainLengthOfCurrentContainerId(location);
	}
	if (terminals[HCHAIN].IsActive())
	{
		
		terminalValues[terminals[HCHAIN].GetId()] = containerYard.GetTopMaxChainLength(location);
	}

	if (terminals[HS].IsActive())
	{
		terminalValues[terminals[HS].GetId()] = containerYard.NumberOfHoisted(location, source);
	}

	if (terminals[LS].IsActive())
	{
		terminalValues[terminals[LS].GetId()] = containerYard.NumberOfLowered(location, source);
	}

	if (terminals[RS].IsActive())
	{
		terminalValues[terminals[RS].GetId()] = containerYard.WillNeedToBeReshuffled(location, containerId);
	}

	if (terminals[GS].IsActive())
	{


		terminalValues[terminals[GS].GetId()] = containerYard.CalculateTightness(location, containerId);
	}

	if (terminals[KS].IsActive())
	{
		int src = source.GetStack();
		int dest = location.GetStack();

		if (src < dest)
			terminalValues[terminals[KS].GetId()] = dest - src;
		else
			terminalValues[terminals[KS].GetId()] = 0;
	}

	if(terminals[ENGY].IsActive())
	{
		terminalValues[terminals[ENGY].GetId()] = containerYard.CalculateEnergyConsumption(source, location, containerId, false);
	}
	
	if(terminals[WGHT].IsActive())
	{
		terminalValues[terminals[WGHT].GetId()] = containerYard.getContainerWeight(containerId);
	}
	if(terminals[NUNC].IsActive())
	{
		terminalValues[terminals[NUNC].GetId()] = containerYard.GetNumberOfUknown(location);

	}
	if (terminals[NPER].IsActive())
	{
		double uknownCount = containerYard.GetNumberOfUknown(location);
		double totalNumberOfContainers = containerYard.GetStackHeight(location);
		if (totalNumberOfContainers==0.0)
		{
			totalNumberOfContainers = 1;
		}
		terminalValues[terminals[NPER].GetId()] = uknownCount/totalNumberOfContainers;
	}
	if (terminals[NRAT].IsActive())
	{
		double unknownCount = containerYard.GetNumberOfUknown(location);
		if(unknownCount==0)
		{
			unknownCount = 1;
		}
		double knownCount = containerYard.GetStackHeight(location) - unknownCount;
		terminalValues[terminals[NRAT].GetId()] = knownCount / unknownCount;
	}

	if(terminals[NGRP].IsActive())
	{
		terminalValues[terminals[NGRP].GetId()] = containerYard.GetNumberOfContainerGroups();
	}

	if (terminals[GRPS].IsActive())
	{
		terminalValues[terminals[GRPS].GetId()] = containerYard.GetContainerGroupSize();
	}


}

double Terminals::GetTerminalValue(int terminalId)
{
	return terminalValues[terminalId];
}



bool Terminals::IsTerminal(string terminalString)
{
	const auto terminal = allowedTerminals.find(terminalString);
	return allowedTerminals.end() != terminal;
}

double Terminals::GetTerminalValue(NodeId terminal) {
	if (terminals[terminal].IsActive())
		return terminalValues[terminals[terminal].GetId()];
}


void Terminals::setActiveGRHTerminals() {
	terminals[HS].SetActive(true);
	terminals[LS].SetActive(true);
	terminals[DIS].SetActive(true);
	terminals[RS].SetActive(true);
	terminals[MIN].SetActive(true);
	terminals[GS].SetActive(true);
	terminals[KS].SetActive(true);
	terminals[SH].SetActive(true);
}
 