#include <iostream>
#include <vector>

using namespace std;

int main(){
	int t;
	cin>>t;
	while(t--){
		int n;
		cin>>n;
		vector<int> b;
		for(int i = 0; i<n-2; i++){
			int x;
			cin>>x;
			b.push_back(x);
		}
		int p=0,f;
		if(b[0]==1) f=0;
		else f=1;
		bool w = true;
		for(int i = 1; i<n-2; i++){
			if(b[i]==1){
				if(p!=f) w=false;
			}else{
				if(p==f){
					p=f;
					f++;
				}
			}
		}
		if(w) cout<<"YES"<<endl;
		else cout<<"NO"<<endl;
	}
}