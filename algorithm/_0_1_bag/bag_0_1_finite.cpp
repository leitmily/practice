#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

int bag_0_1_finite(vector<int>& weights, vector<int>& values, int capacity) {
    if(weights.size() != values.size()) return 0;
    int N = weights.size();
    vector<int> w = {0}, v = {0};
    for(int i = 0; i < N; i++) {
        w.push_back(weights[i]);
        v.push_back(values[i]);
    }
    vector<vector<int>> dp(N + 1, vector<int>(capacity + 1, 0));
    for(int i = 1; i <= N; i++) {
        for(int j = 1; j <= capacity; j++) {
            if(j < w[i])
                dp[i][j] = dp[i - 1][j];
            else {
                dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - w[i]] + v[i]);
            }
        }
    }
    return dp[N][capacity];
}

int bag_0_1_finite2(vector<int>& weights, vector<int>& values, int capacity) {
    if(weights.size() != values.size()) return 0;
    int N = weights.size();
    vector<int> w = {0}, v = {0};
    for(int i = 0; i < N; i++) {
        w.push_back(weights[i]);
        v.push_back(values[i]);
    }
    vector<int> dp(capacity + 1, 0);
    for(int i = 1; i <= N; i++) {
        for(int j = capacity; j >= 1; j--) {
            if(j < w[i])
                dp[j] = dp[j];
            else {
                dp[j] = max(dp[j], dp[j - w[i]] + v[i]);
            }
        }
    }
    return dp[capacity];
}

int main() {
    vector<int> weights = {3, 1,2};
    vector<int> values = {120, 60, 100};
    cout << bag_0_1_finite(weights, values, 5) << endl;
    return 0;
}
