#include "Evaluator.h"
#include <cmath>
#include <sstream>
#include <string>
#include <iostream>
#include "StringUtils.h"
using namespace std;


void Evaluator::Reset()
{
	position = -1;
}

Evaluator::Evaluator(Terminals& terminals) : terminals(terminals)
{
	InitialiseFunctionNodes();
}

void Evaluator::ParseExpression(string expression)
{
	
	StringUtils::trim(expression);
	int expressionSize = count(expression.begin(), expression.end(), ' ')+1;
	parsedExpression.resize(expressionSize);
	constants.clear();
	stringstream stream(expression);

	string node; 
	
	for (int index = 0; index < expressionSize; index++)
	{
		stream >> node;
		const auto& functionNode = functionNodes.find(node);
		if (functionNode != functionNodes.end())
		{
			parsedExpression[index] = functionNode->second;
		}
		else if (terminals.IsTerminal(node))
		{
			int terminalId = terminals.GetTerminalId(node);
			parsedExpression[index] = terminalId + TERMINAL_OFFSET;
		} else
		{
			double constant = stod(node.substr(2));
			constants.push_back(constant);
			parsedExpression[index] = constants.size() - 1 + CONSTANTS_OFFSET;
		}
	}
	position = -1;
}

void Evaluator::InitialiseFunctionNodes()
{
	functionNodes.insert(pair<string, int>("+", 0));
	functionNodes.insert(pair<string, int>("-", 1));
	functionNodes.insert(pair<string, int>("*", 2));
	functionNodes.insert(pair<string, int>("/", 3));
	functionNodes.insert(pair<string, int>("sin", 4));
	functionNodes.insert(pair<string, int>("cos", 5));
	functionNodes.insert(pair<string, int>("pos", 6));
	functionNodes.insert(pair<string, int>("ifpos", 7));
	functionNodes.insert(pair<string, int>("ifgt", 8));
	functionNodes.insert(pair<string, int>("min", 9));
	functionNodes.insert(pair<string, int>("max", 10));
	functionNodes.insert(pair<string, int>("avg", 11));
	functionNodes.insert(pair<string, int>("sqrt", 12));
	functionNodes.insert(pair<string, int>("neg", 13));
}

double Evaluator::Execute()
{
	calls++;
	position++;

	switch (parsedExpression[position]) {
	case ADD:
		return Execute() + Execute();
		break;
	case SUB:
		return Execute() - Execute();
		break;
	case MUL:
		return Execute() * Execute();
		break;
	case DIV: {
		double d1 = Execute();
		double d2 = Execute();
		if (fabs(d2) < 0.000000001)
			return 1;
		else
			return d1 / d2;
		break;
	}
	case SIN:
		return sin(Execute());
		break;
	case COS:
		return cos(Execute());
		break;
	case POS: {
		double d = Execute();
		return (d > 0) ? d : 0;
		break;
	}
	case IFPOS: {
		double v = Execute();
		double d1 = Execute();
		double d2 = Execute();
		return (v >= 0) ? d1 : d2;
		break;
	}
	case IFGT: {
		double v1 = Execute();
		double v2 = Execute();
		double d1 = Execute();
		double d2 = Execute();
		return (v1 > v2) ? d1 : d2;
		break;
	}
	case MIN: {
		double d1 = Execute();
		double d2 = Execute();
		if (d1 < d2)
			return d1;
		else
			return d2;
		break;
	}
	case MAX: {
		double d1 = Execute();
		double d2 = Execute();
		if (d1 > d2)
			return d1;
		else
			return d2;
		break;
	}
	case AVG: {
		double d1 = Execute();
		double d2 = Execute();
		return (d1 + d2) / 2;
		break;
	}
	case SQRT: {
		double d = Execute();
		return (d > 0) ? sqrt(d) : 0;
		break;
	}
	case NEG: {
		double d = Execute();
		return -d;
		break;
	}
	default:
		if (parsedExpression[position] >= CONSTANTS_OFFSET)
			return constants[parsedExpression[position] - CONSTANTS_OFFSET];
		else
			//return (*terminalValues[parsedExpression[position] - TERMINALS])	[iSample];
			return terminals.GetTerminalValue(parsedExpression[position] - TERMINAL_OFFSET);
		break;
	};
}

int Evaluator::GetCalls()
{
	return calls;
}

void Evaluator::ResetCalls()
{
	calls = 0;
}
