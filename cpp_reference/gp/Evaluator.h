#pragma once
#include <vector>
#include <string>
#include <unordered_map>
#include "Terminals.h"
#include <stack>

using namespace std;

class Evaluator
{
private:
	const int TERMINAL_OFFSET = 1000;
	const int CONSTANTS_OFFSET = 2000;
	int position;
	int calls = 0;
	enum Functions { ADD, SUB, MUL, DIV, SIN, COS, POS, IFPOS, IFGT, MIN, MAX, AVG, SQRT, NEG };
	
	Terminals& terminals;
	vector<int> parsedExpression;
	vector<double> constants;
	unordered_map<string, int> functionNodes;
	
public:
	void Reset();
	Evaluator(Terminals& terminals);
	void ParseExpression(string expression);
	void InitialiseFunctionNodes();
	double Execute();
	int GetCalls();
	void ResetCalls();
};

