#--------------------------------------GRUPO 027----------------------------------------------
#							- Joao Tavares  86443
#							- Pedro Antunes 86493
#							- Rui Matos     79100
#---------------------------------------------------------------------------------------------


from   global_functions import *  #this file must be in the same directory as the main file!
from   socket import *
from   select import select
import argparse
import os
import sys
import glob
import random
import glob
import shutil

BUFFER_SIZE = 4194304 #2^22
bs_list = []


#CS:
#1. Connection and Parsing
#2. Auxiliar Functions
#3. User Registration
#4. CS Functions (to support Client interaction)
#5. Client Handler (first contact with the client)
#6. Register BS Connection
#7. Contact a BS
#8. Main

#----1. CONNECTION and PARSING----------------------------------------------------------------

   # PARA TESTES NO TEJO
#CS_PORT = 58011
#CS_PORT = 58011

  # DEFAULT
CS_PORT = 58027        #(58000 + group number)
CS_IP = '127.0.0.1'    #Usado para falar c o nosso proprio servidor dentro do mm pc

# create TCP socket (talks with user)
s_tcp = socket(AF_INET,SOCK_STREAM)
s_tcp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #evitar o errno98
s_tcp.bind(('', CS_PORT))
s_tcp.listen(1)

# create UDP socket as server (receives BSs registrations)
s_udp = socket(AF_INET, SOCK_DGRAM)
s_udp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #evitar o errno98
s_udp.bind((CS_IP, CS_PORT))

# create UDP socket as client (receives info from BSs)
c_udp = socket(AF_INET, SOCK_DGRAM)
c_udp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #evitar o errno98

parser = argparse.ArgumentParser()
parser.add_argument('-p', help='CSport: server port')	# 58011
args = parser.parse_args()

if (args.p != None):
    CS_PORT = int(args.p)
#---------------------------------------------------------------------------------------------


#----2. AUXILIAR FUNCTIONS--------------------------------------------------------------------
#---------------------------------------------------------------------------------------------


#----3. USER REGISTRATION---------------------------------------------------------------------

#Registration_check: Decides if a user will be Authenticated (1), warned that the Password he
#                    used is wrong (2), or Registered as a new user (3)
def reg_check(user):
    filename = cs_user_folder(user[0]) + '.txt'
    if (exists_file(filename)):
        if (read_first_line(filename) == user[1]):
            return 1
        else:
            return 2
    else:
        return 3


#User Authenticated: we need to check whether this was just an ordinary login from and already
#                    registered user, or it was an authentication that will be followed by a
#                    command.
def reg_1(user_info, conn):
    conn.send('AUR OK\n')
    data = conn.recv(BUFFER_SIZE)
    if (data != ''):
        while (data[len(data)-1] != '\n'):
            data += conn.recv(BUFFER_SIZE)
    data.decode()

    user  = user_info[0]
    passw = user_info[1]

    #if we receive more content from the user, we'll evaluate that command
    if (data != ''):
        if(data[0:3]== 'DLU'):   #deluser
            deluser(user, conn)
        elif(data[0:3] == 'BCK'): #backup
            backup(user, passw, data[4:], conn)
        elif(data[0:3] == 'RST'): #restore
            restore(user, data[4:], conn)
        elif(data[0:3] == 'LSD'): #dirlist
            dirlist(user, conn)
        elif(data[0:3] == 'LSF'): #filelist
            filelist(user, data[4:], conn)
        elif(data[0:3] == 'DEL'): #delete
            delete(user, data[4:], conn)
        elif(data[0:4] == 'TEST'): #test
            test(user, conn)
        else:
            print 'ERR\n'
    #else: it was just an ordinary login


#User Password is Wrong
def reg_2(conn):
    conn.send('AUR NOK\n')



#User Not Registered: we'll proceed to register the user
def reg_3(user, conn):
    #create CS/user_nnnnn folder
    create_folder(cs_user_folder(user[0]))
    #create user_nnnnn.txt inside /CS folder
    path = app_path() + '/CS/user_' + user[0] + '.txt'
    create_txt(path, str(user[1]))
    conn.send('AUR NEW\n')
    print 'New user: ' + user[0]
#---------------------------------------------------------------------------------------------


#----4. CS FUNCTIONS--------------------------------------------------------------------------
#   (J)  About deluser:
#        esta de certeza bem implementada, mas no bs, sempre que um bs apagar um user, ele tem de
#        comunicar isso ao cs, para o cs tambem apagar esse bs da pasta do user
#        uma vez q o user sera apagado se a sua pasta estiver vazia (= n haver bs)
def deluser(user, conn):
    path = cs_user_folder(user)

    if is_path_empty(path):
        delete_folder(path)
        filename = 'user_' + str(user[0]) + '.txt'
        delete_txt(filename)
        conn.send('DLU OK\n')

    else:
        conn.send('DLU NOK\n')





def backup(user, passw, data, conn):
    data_process = data.split(' ')
    directory = data_process[0]

    path = cs_user_folder(user) + '/' + directory
    filepath = path + '/IP_port.txt'

	#reads file IP_port.txt if it exists
	#creates folder user_nnnnn if it not exists and create file IP_port.txt
    if (exists_file(path)):
        txt = read_first_line(filepath)
        bs = txt.split(' ')
        ipbs = bs[0]
        portbs = int(bs[1])
    else:
        create_folder(path)
        bs = random.choice(bs_list)
        ipbs = bs[0]
        portbs = bs[1]
        txt = ipbs + ' ' + str(portbs)
        create_txt(filepath, txt)

    message = 'LSU ' + user + ' ' + passw + '\n'
    answer = client_bs(message, ipbs, portbs)
    if (answer == 'LUR OK\n'):
        i=0
        while(data[i] != ' '):
            i+=1
        message = 'BKR ' + ipbs + ' ' + str(portbs) + ' ' + data[i+1:] + '\n'
        conn.send(message)
    if (answer == 'LUR NOK\n'):
        message = 'LSF ' + user + ' ' + directory + '\n'
        bs = random.choice(bs_list)
        answer = client_bs(message, ipbs, portbs)
        processed = answer.decode().split()
        data_process[len(data_process)-1] = data_process[len(data_process)-1].replace('\n','')

		#------
        #Comparar ficheiros que o user pediu p backup com os que o backup mandou
        #Enviamos a diferenca
        nr_files = 0
        files = ''

        data_p_list = []
        n=2
        for i in range(int(data_process[1])):
            fich = data_process[n] + ' ' + data_process[n+1] + ' ' + data_process[n+2] + ' ' + data_process[n+3]
            data_p_list += [fich]
            n+=4

        processed_list = []
        n=2
        for i in range(int(processed[1])):
            fich = processed[n] + ' ' + processed[n+1] + ' ' + processed[n+2] + ' ' + processed[n+3]
            processed_list += [fich]
            n+=4

        fich = ''
        flag_iguais = 0
        for i in range(len(data_p_list)):
            for l in range(len(processed_list)):
                if (data_p_list[i] == processed_list[l]):
                    flag_iguais = 1 #ficheiro esta no backup
            if (flag_iguais != 1):
                #ficheiro n esta no backup
                fich += data_p_list[i] + ' '
                nr_files += 1
            flag_iguais = 0
        #------

        if (nr_files == 0):
            conn.send('BKR EOF\n')
        else:
            message = 'BKR ' + ipbs + ' ' + str(portbs) + ' ' + str(nr_files) + ' ' + fich[:(len(fich)-1)] + '\n'
            conn.send(message)




def restore(user, data, conn):
	direct = cs_user_folder(user) + '/' + data[:len(data)-1]
	if not (exists_file(direct)):
		conn.send('RSR EOF\n')
	else:

		filepath = cs_user_folder(user) + '/' + data[:len(data)-1] + '/IP_port.txt'

		if (exists_file(filepath)):
			msg = 'RSR ' + read_first_line(filepath) + '\n'
			conn.send(msg)



#   (J)  About dirlist:
#        assim que o bs estiver a fazer backups e o cs estiver a guardar as diretorias
#        que ja estao em backup, temos de testar esta funcao. penso q esta bem tho
def dirlist(user,conn):
    path = cs_user_folder(user)
    if (is_path_empty(path)):
        conn.send('LDR 0\n')
    else:
        lista = os.listdir(path)
        dirs = ''
        for i in lista:
            dirs += ' ' + i
        msg = 'LDR ' + str(len(lista)) + dirs + '\n'
        conn.send(msg)




def filelist(user, msg, conn):
    #2, listar os ficheiros q estao guardados nessa diretoria
    #     implementacao: ou vamos contactar o bs que os guarda e pedir essa lista de ficheiros
    #                    ou entao o proprio cs na diretoria descrita em 1, tem essa lista

    directory = cs_user_folder(user) + '/' + msg[:len(msg)-1]
    if not (exists_file(directory)):
        conn.send('LFD NOK\n')
    else:
        #ler ficheiro com o IP e Port onde esta esse backup
        intel = (read_first_line(directory + '/IP_port.txt')).split(' ')
        ip    = intel[0]
        port  = int(intel[1])

        message = 'LSF ' + user + ' ' + msg
        data = client_bs(message, ip, port)
        if (data[4] == '0'):
            conn.send('LFD NOK\n')
        else:
        	message = 'LSF ' + ip + ' ' + str(port) + ' ' + data[4:] + '\n'
        	conn.send(message)




#(working on it)
def delete(user, msg, conn):
    directory = cs_user_folder(user) + '/' + msg[:len(msg)-1]
    if not (exists_file(directory)):
        conn.send('DDR NOK\n')
    else:
        #ler ficheiro com o IP e Port onde esta esse backup
        intel = (read_first_line(directory + '/IP_port.txt')).split(' ')
        ip    = intel[0]
        port  = int(intel[1])

        message = 'DLB ' + user + ' ' + msg
        data = client_bs(message, ip, port)


        #Answering client
        if(data == 'DBR OK\n'):
            if (is_path_empty(directory)):
                os.rmdir(directory)
            else:
                shutil.rmtree(directory)
            conn.send('DDR OK\n')
        elif(data == 'DBR NOK\n'):
            conn.send('DDR NOK\n')

#---------------------------------------------------------------------------------------------


#----5. CLIENT HANDLER------------------------------------------------------------------------

#MAIN AUTHENTICATION FUNCTION: Authenticates the user and evaluates whether the user
#                              made a regular login or he's trying to execute a command
def client_handler(conn):
    data = conn.recv(BUFFER_SIZE)
    if (data != ''):
        while (data[len(data)-1] != '\n'):
            data += conn.recv(BUFFER_SIZE)
    data.decode()
    if(data[0:3] == 'AUT'): #login
        user = data[4:9],data[10:19]
        status = reg_check(user)
        if status == 1:
            reg_1(user, conn)

        elif status == 2:
            reg_2(conn)

        elif status == 3:
            reg_3(user, conn)

    else:
        print 'ERR\n'
#---------------------------------------------------------------------------------------------


#----6. REGISTER BS CONNECTION----------------------------------------------------------------

def reg_backup():   #--
    global bs_list
    data, addr = s_udp.recvfrom(BUFFER_SIZE)
    if(data[0:3] == 'REG'):
    	newdata = ''
    	i = 4
    	while i < len(data):
    		if (data[i] != '\n'):
    			newdata += data[i]
    		i += 1
        bs = newdata.split(' ')
        bs[1] = int(bs[1])
        bs_list += [bs] #registers BS
        s_udp.sendto('RGR OK\n', addr)
        print '+BS: ' + (data[4:24]).decode()
    else:
        s_udp.sendto('RGR NOK\n', addr)
        print 'ERR\n'
#---------------------------------------------------------------------------------------------


#----7. CONNECT to a BS-----------------------------------------------------------------------

def client_bs(message, ipbs, portbs):
    #sock = socket(socket.AF_INET, SOCK_DGRAM) # UDP
    #sock.sendto(message, (ipbs, portbs))
    c_udp.sendto(message, (ipbs, portbs))
    data, addr = c_udp.recvfrom(BUFFER_SIZE)
    #fechar socket
    return data.decode()
#---------------------------------------------------------------------------------------------

#----8. MAIN----------------------------------------------------------------------------------
#Funcao que processa o pedido tcp/udp no CS:
def main():

    folder_path = app_path() + '/CS'
    if not (os.path.isdir(folder_path)):
        create_folder(folder_path)


    while 1:
        inS, _ , _ = select([s_tcp, s_udp],[],[])
        for s in inS:
            #TCP connection as server:
            if (s is s_tcp):
                conn, addr = s_tcp.accept()
                pid = os.fork()
                if (pid == 0):       #FILHO
                    #s_tcp.close()
                    client_handler(conn)
                    #matar o filho

            #UDP Connection as server:
            elif (s is s_udp):
                reg_backup()
            else:
                print 'unknown socket: ' + s

#---------------------------------------------------------------------------------------------
main()
