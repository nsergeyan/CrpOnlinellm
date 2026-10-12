#pragma once

#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include "ContainerYard.h"
#include "Terminal.h"

using namespace std;

//enum NodeId
//{
//	SH, // stack height node
//	EMP, // number of empty places in stack
//	CUR, // ID of the current container to be relocated
//	
//	DUR, // time required to transfer the stack to the selected stack
//	DIS, // the distance in stacks between the current stack and the destination stack (we have to think how to do this, should be applicable for multibays) <- skip this one
//	
//	RI, // the reshuffle index, i.e. the number of nodes that need to be reallocated before the container which is put on top
//	MIN, // return the smallest index in the stack
//	AVG, // average of indices in the stack
//	
//	REM, // remaining stacks before the next stack is at the top
//	NEXT, // contains next container -> 1 if the stack does not contain the next container, 0 otherwise
//	BLKD, // number of containers that will be blocked after reallocating top container from the stack with next container
//	DIFF, // difference between a container with the highest priority in the stack and the one that needs to be relocated //TODO: Now it can be a positive and negative value, is it ok?
//	EMPTY, // if stack is empty -> 1, 0 otherwise
//	WL, // number of well-placed containers in the stack
//	NL, // number of non-placed containers in the stack
//	DSM,
//
//	NRC, // number of remaining containers with the current index
//	NCURR, // number of current indices in the stack
//	NSC, // number of stacks in which the container with the current id appears
//	HC, // height of the container with the current index
//	DIFFIND, // number od different indices in the stack
//	CHAIN, // lenght of the chain with the same priority of the current id
//	HCHAIN, //top chain length of the same index    
//};


enum NodeId
{
	SH, // stack height node
	DUR, // time required to transfer the stack to the selected stack
	RI, // the reshuffle index, i.e. the number of nodes that need to be reallocated before the container which is put on top
	MIN, // return the smallest index in the stack
	DIS, // the distance in stacks between the current stack and the destination stack (we have to think how to do this, should be applicable for multibays) <- skip this one
	EMP, // number of empty places in stack
	AVG, // average of indices in the stack

	REM, // remaining stacks before the next stack is at the top
	NEXT, // contains next container -> 1 if the stack does not contain the next container, 0 otherwise
	BLKD, // number of containers that will be blocked after reallocating top container from the stack with next container
	DIFF, // difference between a container with the highest priority in the stack and the one that needs to be relocated //TODO: Now it can be a positive and negative value, is it ok?
	EMPTY, // if stack is empty -> 1, 0 otherwise
	WL, // number of well-placed containers in the stack
	NL, // number of non-placed containers in the stack
	CUR, // ID of the current container to be relocated
	DSM,

	
	NRC, // number of remaining containers with the current index
	NCURR, // number of current indices in the stack
	NSC, // number of stacks in which the container with the current id appears
	HC, // height of the container with the current index
	DIFFIND, // number od different indices in the stack
	CHAIN, // lenght of the chain with the same priority of the current id
	HCHAIN, //top chain length of the same index

	//connected with GA
	HS, //Number of tiers hoisted when moving reshuffled container to stack s
	LS, //Number of tiers lowered when moving reshuffled container to stack s
	// XS - Number of rows trolleyed when moving reshuffled container to stack s - same as DIS
	RS, //= 1 if container c must be reshuffled again if it is placed on stack s (binary)
	//TS - Lowest numbered container in stack s - same as MIN
	GS, //Tightness = (ts – c – 1)/C (lower case c in numerator and upper case C in denominator)
	KS, //Amount of trolley movement away from truck lane if container c reshuffled to stack s (= 0 if trolley moves toward truck lane when container reshuffled to stack s)
	//NS - Number of containers in stack s - same as SH

	ENGY, // energy spent on the move
	WGHT, // weight of container


	// for online only
	NUNC, // number of containers on stack for which we do not know their ID
	NPER, //percentage of unknown container ids on stack
	NRAT, // ratio between known and unknown container IDs on stack.

	NGRP, //number of container groups
	GRPS, // container group size
};


class Terminals
{
private:
	vector<Terminal> terminals;
	vector<double> terminalValues;
	unordered_map<string, int> activeTerminals;
	unordered_set<string> allowedTerminals;
	
	
public:
	Terminals();
	void initialiseTerminals();
	int GetTerminalId(const string& terminal);
	void CalculateTerminals(ContainerYard& containerYard, int containerId, Location& source, Location& location);
	double GetTerminalValue(int terminalId);
	double GetTerminalValue(NodeId terminal);
	void setActiveGRHTerminals();
	bool IsTerminal(string terminalString);
};

