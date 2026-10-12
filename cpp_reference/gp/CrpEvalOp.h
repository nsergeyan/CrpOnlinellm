#pragma once
#include "ECF/ECF.h"
#include "ECF/EvaluateOp.h"
#include <DataSetLoader.h>

#include "EvaluationUtils.h"
#include "HeuristicFactory.h"
#include <map>
#include <vector>

#include "FitnessApproximationSurrotate.h"
#include "PythonSocketClient.h"
#include "PythonSocketServer.h"


class CrpEvalOp :
	public EvaluateOp
{
private:
	StateP state_;
	std::shared_ptr<DataSet> ds;
	std::shared_ptr<DataSet> surrogate;
	std::string project_dir_;
	string subset;
	string criterion;
	HeuristicFactory factory;
	std::shared_ptr<EvaluationUtils> utils;
	PythonSocketServer server;
	PythonSocketClient client;

	FitnessApproximationSurrotate approximateionSurrogate;

public:
	map<string, vector<int>> fitnessValues;
	std::vector<string> ordered_individuals;


	CrpEvalOp(std::shared_ptr<EvaluationUtils> utils, int port);
	bool initialize(StateP) override;
	FitnessP evaluate(IndividualP individual) override;
	FitnessP evaluateSurrogate(IndividualP individual);
	void registerParameters(StateP) override;
	void changeDataSet();
	void generationPassed();
	void resizeDataSetToMaximumSize();
};

typedef boost::shared_ptr<CrpEvalOp> CrpEvalOpP;