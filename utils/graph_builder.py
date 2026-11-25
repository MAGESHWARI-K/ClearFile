import plotly.graph_objects as go
import math

def build_graph(extracted, findings):
    docs=list(extracted.keys())
    fields=list(dict.fromkeys(f['field'] for f in findings))
    fig=go.Figure()
    if not docs:
        fig.add_annotation(text='Upload documents to see their relationships',showarrow=False,font=dict(size=15,color='#625B57'))
        fig.update_layout(height=360, xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig
    doc_pos={d:(math.cos(2*math.pi*i/max(len(docs),1)), math.sin(2*math.pi*i/max(len(docs),1))) for i,d in enumerate(docs)}
    field_pos={f:(0.42*math.cos(2*math.pi*i/max(len(fields),1)+.5),0.42*math.sin(2*math.pi*i/max(len(fields),1)+.5)) for i,f in enumerate(fields)}
    for item in findings:
        fx,fy=field_pos[item['field']]
        for d in item['documents']:
            dx,dy=doc_pos[d]; color='#71806A' if item['status']=='Match' else '#B64A4A'
            fig.add_trace(go.Scatter(x=[dx,fx],y=[dy,fy],mode='lines',line=dict(color=color,width=2),hoverinfo='text',text=[f"{d} → {item['field']}: {item['values'].get(d,'')}"]*2,showlegend=False))
    fig.add_trace(go.Scatter(x=[p[0] for p in doc_pos.values()],y=[p[1] for p in doc_pos.values()],mode='markers+text',text=docs,textposition='bottom center',marker=dict(size=28,color='#6E1724',line=dict(color='#F8F3EA',width=2)),name='Documents',hovertemplate='%{text}<extra></extra>'))
    if fields:
        colors=['#71806A' if next((f['status'] for f in findings if f['field']==field),'')=='Match' else '#B64A4A' for field in fields]
        fig.add_trace(go.Scatter(x=[p[0] for p in field_pos.values()],y=[p[1] for p in field_pos.values()],mode='markers+text',text=fields,textposition='middle center',marker=dict(size=20,color=colors,line=dict(color='white',width=1)),name='Compared fields',hovertemplate='%{text}<extra></extra>'))
    fig.update_layout(height=500,margin=dict(l=20,r=20,t=20,b=40),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(visible=False,range=[-1.4,1.4]),yaxis=dict(visible=False,range=[-1.3,1.3]),legend=dict(orientation='h',y=-.1),showlegend=True)
    return fig
