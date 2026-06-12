JJ -11\ be eA PRESENTACAO FINAL 

AAPRESENTACAO MATUTINO E NOTURNO: 15/06/2026 (TURMA B e 

## AAPRESENTACAO MATUTINO: 11/06/2025 (TURMA A) 

## PROVA MATUTINO E NOTURNO: 22/06/2026 (TURMAB e UN) PROVA MATUTINO: 18/06/2026 (TURMA A) 

## SCHEDULE DA SIMULAGAO: 

ATENCAO: A SIMULAGAO CONSIDERA QUE AS RNs ESTAO DE ACORDO COM O ESPECIFICADO NO PROJETO E DEVEM ESTAR EM PLENO FUNCIONAMENTO ~~.~~ 

A comunicagao com o supervisor sera por socket TCP na porta 8000 a cada 10s Os SERVERS nao devem aguardar mensagem (RECV) com retorno, apenas (-)¢-Toi0 f-] ees) 1) 1 PI[DASHBOARD][PARA][TESTE][ABAIXO] 

PAYLOAD: 

{ "server ~~_u~~ uid": "michel ~~_1~~ ", "hostname": "miche ~~l_1~~ .farm.local", "role": "master", "task": "“performanc ~~e_~~ report", "timestamp": "2026 ~~-~~ @6 ~~-~~ 08T12:34:56Z", "message ~~i~~ d": "alb2c3d4 ~~-~~ e5f6 ~~-~~ 7890 ~~-~~ abcd ~~-e~~ f1234567890", "“payloa ~~d_~~ version": "sprint4 ~~-~~ monitor", "performance": { "system": { "uptime ~~_s~~ econds": 12345, "lo ~~ad~~ _aver ~~agi~~ m":e_ 3.20, "lo ~~ad~~ _ave ~~ra5~~ gem": 2.50, "cpu": { "usage ~~p~~ ercent": 85.42, "count ~~_l~~ ogical": 8, "count ~~_p~~ hysical": 4 }, "memory": { "total ~~_m~~ b": 16384, "available mb": 8192, "percent ~~_u~~ sed": 62.18, "memory ~~_u~~ sed": 8000 }, 

"disk": { "total ~~g~~ b": 512.0, "free gb": 250.0, "percent ~~_u~~ sed": 45.@ } }s "farm ~~_s~~ tate": { "workers": { "total registered": 6, "workers ~~u~~ tilization": 4, "workers ~~a~~ live": 6, "workers ~~i~~ dle": 2, "workers ~~b~~ orrowed": 1, "workers ~~r~~ eceived": 1, "workers failed": @, "workers ~~h~~ ome": 5, "workers available ~~c~~ apacity": 2, "borrowed ~~_w~~ orkers": [ { "direction": "out", "“pee ~~r_~~ uuid": "michel ~~_2~~ " }, { "direction": "in", "“pee ~~r_~~ uuid": "michel ~~_2~~ " } ] hs "tasks": { "tasks ~~_p~~ ending": 42, "tasks ~~r~~ unning": 4, "tasks ~~c~~ ompleted": 150, "tasks failed": 3, "olde ~~st~~ _t ~~as~~ k_ ~~a~~ s":ge 312 } }, "config thresholds": { "max ~~_t~~ ask": 100, "war ~~n_~~ cpu ~~_p~~ ercent": 85, "warn ~~_m~~ emory ~~_ p~~ ercent": 85, "release task": 60 }s "neighbors": [ { "server ~~_u~~ uid": "michel ~~2~~ ", "status": "available", "las ~~t_~~ heartbeat": "2026 ~~-~~ @6 ~~-~~ 08T12:34:56Z" } ] } } 

## Uso do Supervisor de Métricas do Cluster 

Foi implementado um Supervisor de Meétricas para monitorar, em tempo real, os projetos desenvolvidos na disciplina. Esse supervisor recebe relatorios de desempenho via TCP e apresenta as informagdes em um dashboard web acessivel pelo navegador. 

Descric¢ao dos itens do payload: 

||Campo|Campo|Campo|||||Tipo|Tipo|Descrigao|Descrigao|Descrigao|Descrigao|Descrigao|Descrigao|Descrigao|Descrigao||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|serve~~r_u~~uid||||string||||||Identificador Unico do|||servidor no cluster|||||||||(ex:|
|||||||||||“michel_1")|||||||||||||
|hostname||||||||||Nome DNS do no (ex: "michel_1.farm.local")|||||||||||||
|role||||||||||Papel do no no cluster|||("master")||||||||||
|task||||||||||Tipo de relatdrio enviado||||("performance~~_r~~eport")|||||||||
|timestamp||||string||||||Momento da coleta no|||formato||||||||||
|||||(ISO~~-~~8601)|||||||YYY~~Y-~~MM~~-~~DDTHH:MM:SSZ|||||||||||||
|message ~~_i~~d||||string||||||Identificador unico da|||mensagem||||||||||
|||||(UUID)|||||||||||||||||||
|payload~~_v~~ersion||||string||||||Versaodoschema do payload||||||||(ex:|||||
|||||||||||“sprint~~4-~~monitor~~-v~~2")|||||||||||||
|performance.system|||||||||||||||||||||||
||Campo|||||||Tipo||||Descrigao|||||||||||
|uptim~~e_~~seconds||||||||||Tempo de atividade|do no|||||em||segundos|||||
|loa~~d_~~averag~~e_~~1m||||||||||Média de load daCPU|||nos|||ultimos 1|||minuto||||
|loa~~d_~~averag~~e_~~5m||||||||||Média de load daCPU|||nos|||ultimos 5 minutos|||||||
|cpu.usage~~_p~~ercent||||||||||PercentualdeusodaCPU||||||(0~~-~~100)|||||||



|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical|cpu.count_logical||||||Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|Numero de CPUs ldgicas (threads)|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|cpu.count~~_p~~hysical|||||||||||||||||||Numero deCPUs fisicas|||||||(cores)|||||
|memory.total_mb|||||||||||||||||||Memoria RAM total em||||||MB||||||
|memory.availabl~~e_~~mb|||||||||||||||||||Memoria RAM disponivel em||||||||||MB||
|memory.percent~~_~~used|||||||||||||||||||Percentual de uso|da||||memoria (0~~-~~100)|||||||
|memory.memory~~_u~~sed|||||||||||||||||||Memoria RAM utilizada||||||em|||MB|||
|disk.total_gb|||||||||||||||||||Espagoem disco total em GB||||||||||||
|disk.fre~~e_~~gb|||||||||||||||||||Espacoem disco livre|||||em GB|||||||
|disk.percen~~t_~~used||||||||||||||||float|||Percentual de uso|do||||disco||||(0~~-~~100)|||
||||||||||||||||||||||||||||||||
||||||||||||||||||||||||||||||||
||||Campo||||||||||||||Tipo|||||Descrigao|||||||||
|total_registered|||||||||||||||||||Total de workers atualmente||||||||||registrados no no||
|workers_~~ut~~ilization|||||||||||||||||||Workers ocupados||no momento|||||||||(executando|
||||||||||||||||||||tarefas)||||||||||||
|workers~~_a~~live|||||||||||||||||||Workers considerados vivos/respondendo||||||||||||
|workers ~~_i~~dle|||||||||||||||||||Workers ociosos disponiveis||||||||||para novas tarefas||
|worker~~s_~~borrowed|||||||||||||||||||Workers que este|no|||emprestou|||||||para outros nos|
|workers~~_r~~eceived|||||||||||||||||||Workers que este|no|||recebeu emprestados de||||||||
||||||||||||||||||||outrosnds||||||||||||



**==> picture [449 x 639] intentionally omitted <==**

**----- Start of picture text -----**<br>
|||||||||||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|workers|_f|ailed|Workers|que|falharam|
|worker|s_|home|Workers|nativos|do|servidor|(sem|empréstimos)|
|workers|_a|vailabl|e_|capa|Capacidade|ociosa|total|(=|workers|_i|dle)|
|city|
|borrowed|_w|orkers|array|Lista|de workers|emprestados|com|
|origem/destino|
|Campo|Tipo|Descrigao|
|direction|Diregao|do|empréstimo:|"out"|(emprestou|para|
|outro)|ou|"in"|(recebeu|de|outro)|
|peer|_u|uid|string|serve|r_u|uid|do|no|na|outra|ponta|do empréstimo|
|Campo|Tipo|Descrigao|
|task|s_|pending|Tarefas|aguardando|execugao|
|task|s_|running|Tarefas em|execugao|no|momento|
|task|s_|completed|Total|de|tarefas|concluidas|
|tasks|_f|ailed|Total|de|tarefas|com|falha|
|oldes|t_|tas|k_|age|_s|int|Idade|da|tarefa|pendente|mais|antiga|(segundos)|
|Campo|Tipo|Descrigao|
|no|saturado|
|max_task|-—|Numero|maximo|de|tarefas|antes|de|consideraro|

**----- End of picture text -----**<br>


|warn~~_c~~pu~~_p~~ercent||Percentual deCPU para disparar alerta (ex: 85)|
|---|---|---|
|warn~~_~~memory~~_p~~ercent||| int|Percentual de memoria para disparar alerta (ex:<br>85)|
|release~~_t~~ask|int|Threshold para liberar workers emprestados|



performance.neighbors|[] 

|Campo|Tipo|Descrigao|
|---|---|---|
|serve~~r_u~~uid||Identificadordo no vizinho|
|status||Status do vizinho: "available" ou "unavailable"|
|las~~t_~~heartbeat|string<br>(ISO~~-~~8601)|Timestamp do ultimo heartbeat recebido do vizinho|



## Como enviar dados para o Supervisor 

Para testar o seu projeto, vocé deve: 

1. Enviar os dados de métricas em formato JSON, seguindo o template definido acima. 2. Abrir uma conexao TLS sobre TCP com o supervisor. 3. Enviar o JSON pela conexao estabelecida. 

4. Nao utilizar HTTP para esse envio. 

5. Nao aguardar resposta da aplicagao apds o envio. O cliente deve apenas conectar, enviar os dados e encerrar a conexao. 

Parametros da conexao: 

- e Host: nuted ~~-i~~ a.dev e Porta: 443 e Protocolo: TLS sobre TCP e SNI: nuted ~~-i~~ a.dev 

## Exemplo de configuragao no cddigo: 

TC ~~P_~~ SOCKET ~~_H~~ OST = "nuted ~~-~~ ia.dev" TC ~~P_~~ SOCKET ~~_P~~ ORT = 443 TC ~~P_~~ SOCKET ~~_T~~ LS = True TC ~~P_S~~ OCKET ~~_S~~ NI = “nuted ~~-~~ ia.dev" 

Importante: 

- e Nao use caminhos como /supervisor/colector ou /supervisor no socket TCP. 

- e Emconexoes TCP, 0 endpoint é definido apenas por host e porta. 

- e Nao use bibliotecas HTTP para enviar o payload. e Ocliente deve apenas abrir a conexao, enviar o JSONe finalizar. e Os servers nao devem aguardar mensagem de retorno com recv. 

## Como visualizar o Dashboard 

Todas as métricas enviadas pelos projetos sao agregadas e exibidas em um painel visual interativo. 

Para acompanhar o comportamento do cluster, acesse: 

- e URL do Dashboard: ~~https://nuted-ia.dev/supervisor/dashboard/~~ 

Ao abrir esse enderego no navegador, vocé podera: 

- e Visualizar a topologia dos nos, servers e workers; e Acompanhar o consumo de CPU, memoria, disco e filas de tarefas por servidor; e Ver o estado dos workers, incluindo ativos, ociosos, emprestados e com falha; e Identificar gargalos e nos sobrecarregados em tempo real. 

Cada vez que seu projeto enviar novas métricas pela conexao TLS/TCP configurada, o dashboard sera atualizado automaticamente, permitindo a validagaéo e depuragao do comportamento distribuido da sua aplicagao. 

## Observagao sobre os identificadores dos nos 

Os valores michel_1 e michel_2 representam identificadores de farms em execugao no ambiente do professor e devem ser usados no campo serve ~~r_u~~ uid do payload. Esses valores nao fazem parte do enderego de conexao com o supervisor. 

## EXEMPLO DO DASHBOARD 

**==> picture [347 x 682] intentionally omitted <==**

**----- Start of picture text -----**<br>
esesessos SUPERVISORProf. Michel Junio - SistemasMW FARMDistribuid @ 2 Down /1 High CPU .* @- Alertas00:54:19~Ativos<br>Timeaut de Né Morto (s Escala de Threshold<br>ge eo ee ne<br>MASTERS ATIVOS TAREFAS PENDENTES TOTAL WORKERS WORKERS EMPRESTADOS<br>CPU MEDIA (% CPU MAXIMA (%) MEMORIA MEDIA (%) MAX TAREFAS/NO<br>56.1 100.0 Gh 54.8 sh 139<br>CG)<br>ca MEMORIA TOTAL (MB) CPUS LOGICAS DISCO TOTAL (GB)<br>co 48918 32 *.Q| 1497.5<br>° m<br>al aan<br>Ml Rece a<br>{ ‘<br>H P HISTORICO TARE<br>\<br>||<br>{<br>:<br>WING |<br>SSSt\ Ss eeWAN SS...™<br>wn<br>NOS DA INFRAESTRUTURA (DETALHES)<br>S michel_1 [up = @ SERVER_1 =<br>Tarefas CPU MEM arefas CPU MEM Tarefas CPU MEM Tarefas CPL MEM<br>4 12% 42% 139 100% 67% 16 24% 83% 3 4% 83%<br>performance _repert4:15.754 db73944d performance repers4:05.155 $9466030 performance _repOrts:23.429 @2e6st4e performance reperts:22.311 aS651d64<br>at 12.2% 42.4% 1329/9 100.0% 67.2% 24.0% 82.8% 3/8 4.2% (8/4) 82.8%<br>(8/4) (usa) (w/a) Workers TAYA/YE/R<br>th 1.22/2.50 3h 19.00/2.50 @h 0.00/0.00 oe<br>névia (a) Moméra (nt sacendin (ht) Tol :8075 / Misp:17R6 / Use:6689<br>Tot :16384 / Disp:#192 / Use:Be@ Tot:163u4 / Disp:#192 / Use:Be8e Tot:8075 / Disp:1389 / Use:s6e6 Saco ft)<br>ct 0 (6B) Jot 236.8 / Livi166.2 / 29.4%<br>Tot:512.0 / Liv:250.0 / 45.0% Tot:512.0 / Liv:250.0 / 45.0% Tot:236.8 / Liv:166.2 / 29.8%<br>150.0 00:54:15 1 150.8 00:54:05 15.0 20:45:23 1<br>**----- End of picture text -----**<br>


