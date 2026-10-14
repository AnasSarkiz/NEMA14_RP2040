#include <vector>
#include <queue>
#include <cmath>
#include <cstdint>
#include <algorithm>
#include <limits>
struct Q {double f,g;int32_t id;bool operator<(const Q&o)const{return f!=o.f?f>o.f:(g!=o.g?g>o.g:id>o.id);}};
extern "C" int fast_route(int n,int layers,const uint8_t*wire,const uint8_t*soft,const uint8_t*viafree,const uint8_t*existing,const double*h,const int32_t*starts,int ns,const uint8_t*goal,double searchweight,double softcost,int phase,int phase_layer,double inner_cost,int limit,int32_t*out,int outsize,int*expanded){
 const int plane=n*n,total=plane*layers;std::vector<double>best(total,std::numeric_limits<double>::infinity());std::vector<int32_t>prev(total,-1);std::priority_queue<Q>heap;
 for(int i=0;i<ns;++i){int id=starts[i];best[id]=0;prev[id]=-2;heap.push({searchweight*h[id%plane],0,id});}
 int end=-1;*expanded=0;int dx[8]={1,-1,0,0,1,1,-1,-1},dy[8]={0,0,1,-1,1,-1,1,-1};
 auto push=[&](int q,int from,double g){if(g<best[q]){best[q]=g;prev[q]=from;heap.push({g+searchweight*h[q%plane],g,q});}};
 while(!heap.empty()){
  Q q=heap.top();heap.pop();if(q.g!=best[q.id])continue;if(goal[q.id]){end=q.id;break;}if(++*expanded>limit)break;
  int z=q.id/plane,p=q.id%plane,y=p/n,x=p%n;
  for(int d=0;d<8;++d){int xx=x+dx[d],yy=y+dy[d];if(xx<0||yy<0||xx>=n||yy>=n)continue;int p2=yy*n+xx,id=z*plane+p2;if(wire[id])continue;if(dx[d]&&dy[d]&&(wire[z*plane+y*n+xx]||wire[z*plane+yy*n+x]))continue;double dc=dx[d]&&dy[d]?std::sqrt(2.0):1.0;push(id,q.id,q.g+dc*(z==phase_layer?(phase?12:inner_cost):1)+(soft[id]?softcost:0));}
  if(existing[p]||viafree[p])for(int zz=0;zz<layers;++zz){int id=zz*plane+p;if(zz!=z&&!wire[id])push(id,q.id,q.g+45+(soft[id]?softcost:0));}
 }
 if(end<0)return 0;std::vector<int32_t>path;for(int cur=end;cur>=0;cur=prev[cur]){path.push_back(cur);if(prev[cur]==-2)break;}if((int)path.size()>outsize)return -1;std::reverse(path.begin(),path.end());std::copy(path.begin(),path.end(),out);return path.size();
}
