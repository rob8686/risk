import yfinance as yf
import numpy as np

class Var():
    def __init__(self, fx_converted_df, yf_dict):
        self.fx_converted_df = fx_converted_df
        self.yf_dict = yf_dict
        self.percent_return_df = self.fx_converted_df.pct_change().dropna()
        self.np_percent_return = self.percent_return_df.to_numpy()
        #hist = hist_with_date[:,1:]  
        self.weights = self.position_weights()
        self.np_weighted_returns = np.dot(self.weights, self.np_percent_return)

    def position_weights(self):
        weights = []
        for col in self.fx_converted_df.columns:
            weight = self.yf_dict[col][1]
            weights.append(weight)
        weights_array = np.asarray(weights)
        print(weights_array)
        print(self.np_percent_return)
        return weights_array

    def perc_return(self):
        returns = np.diff(self.fx_converted_df,axis=0)
        print(returns)
        perc_returns = returns / self.fx_converted_df
        print(perc_returns)
        print(self.np_percent_return)
        return perc_returns

    
    def parametric_var():
        pass


#def var(weights, data):
def var(fx_converted_df, yf_dict):
    print('Market Risk!')
    print(fx_converted_df)
    print(yf_dict)

#weighted_return_df = pd.DataFrame()
#self.positions[self.benchmark] = [1, 1]

#for ticker in self.positions:
    #percent_aum = self.positions[ticker][1]
    #weighted_return_df[ticker] = self.percent_return_df[ticker] * percent_aum 

