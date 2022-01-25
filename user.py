#--------------------------------------GRUPO 027----------------------------------------------
#							- Joao Tavares  86443
#							- Pedro Antunes 86493
#							- Rui Matos     79100
#---------------------------------------------------------------------------------------------


from   global_functions import *  #READ ME: this file must be in the same directory as the main file!
from   datetime import datetime
from   socket import *
import argparse
import os
import time

BUFFER_SIZE = 1024

curr_user   = 0      #current user
curr_pass   = 0      #current user's password
logged      = 0      #flag (user logged = 1, user not logged = 0)




#USER:
#1. Connection and Parsing
#2. Contact Servers (CS and BS)
#3. Auxiliar Functions
#4. Main Functions
#5. Main


#----1. CONNECTION and PARSING----------------------------------------------------------------

   # DEFAULT
CS_PORT = 58027      # DEFAULT 58027 (58000 + group number)
CS_NAME = None
CS_IP = '127.0.0.1'  # DEFAULT usado para falar com o CS dentro do mm pc

parser = argparse.ArgumentParser()
parser.add_argument('-n', help='CSname: client name')   # tejo
parser.add_argument('-p', help='CSport: client port')   # 58011 - porto para teste do server tejo
args = parser.parse_args()

if(args.n != None):
    CS_NAME = args.n + '.ist.utl.pt'

if(args.p != None):
    CS_PORT = int(args.p)
#---------------------------------------------------------------------------------------------


#----2. CONTACT SERVERS - BS and CS--------------------------------------------------------------

#This functions receives the message we want to send to CServer and returns its reply
def contact_server(message):
    global CS_IP
    s = socket(AF_INET, SOCK_STREAM)
    if(CS_NAME != None):
        CS_IP = gethostbyname(CS_NAME)
    s.connect((CS_IP, CS_PORT))
    aut_msg = 'AUT ' + str(curr_user) + ' ' + str(curr_pass) + '\n'
    s.sendall(aut_msg)
    aut_reply = s.recv(BUFFER_SIZE)
    if (aut_reply != 'AUR OK\n'):
        if (curr_user == 0):
            s.close()
            return '-1'
        else:
            s.close()
            return '-2'
    else:
        s.sendall(message)
        data = s.recv(BUFFER_SIZE)
        while (data[len(data)-1] != '\n'):
            data = data + s.recv(BUFFER_SIZE)
        s.close()
        return data.decode()


#This functions receives the message we want to send to BServer and returns its reply
def contact_bs(bs_ip, bs_port):
    #cria o socket
    bs_sock = socket(AF_INET, SOCK_STREAM)
    bs_sock.connect((bs_ip, int(bs_port)))
    #autentica
    aut_msg = 'AUT ' + str(curr_user) + ' ' + str(curr_pass) + '\n'
    bs_sock.sendall(aut_msg)
    aut_reply = bs_sock.recv(BUFFER_SIZE)

    if (aut_reply != 'AUR OK\n'):
        if (curr_user == 0):
            bs_sock.close()
            return '-1'
        else:
            bs_sock.close()
            return '-2'
    #se estiver bem autenticado, manda a msg e recebe a resposta
    return bs_sock
#---------------------------------------------------------------------------------------------


#----3. AUXILIAR FUNCTIONS--------------------------------------------------------------------

#This function returns True if there's a logged user and False otherwise
def check_login():
    if (logged == 0):
        return False
    elif (logged == 1):
        return True


#This function evaluates an error related to the authentication of the user on the CServer
def aut_error(error):
    if (error == '-1'):
        print '   There is no logged user\n'
    elif (error == '-2'):
        print '   Authentication error for the user\n'
    else:
        print '   Erro nao documentado'

#---------------------------------------------------------------------------------------------


#----4. MAIN FUNCTIONS------------------------------------------------------------------------

def login(msg):
    message = 'AUT' + msg + '\n'
    global CS_IP, curr_user, curr_pass, logged
    curr_user = msg[1:6]
    curr_pass = msg[7:15]
    logged = 1

    s = socket(AF_INET, SOCK_STREAM)
    if(CS_NAME != None):
        CS_IP = gethostbyname(CS_NAME)
    s.connect((CS_IP, CS_PORT))
    s.sendall(message.encode())
    data = s.recv(BUFFER_SIZE)
    s.close()

    if(data.decode()[:7] == 'AUR NEW'):
        print '   User "' + curr_user + '" created\n'
    elif(data.decode()[:6] == 'AUR OK'):
        print '   User "' + curr_user + '" logged in\n'
    else:
        print '   Wrong password for ' + curr_user + '\n'



def deluser():
    data = contact_server('DLU\n')
    if (data == '-1' or data == '-2'):
        aut_error(data)
    elif (data == 'DLR OK\n'):
        print '   User successfully deleted\n'
    elif (data == 'DLR NOK\n'):
        print '   User has backed up files, cannot be deleted\n'



def backup(msg):
    path = app_path() + '/' + msg     #pasta
    if not(exists_file(path)):
        print '   There is no such directory to backup\n'
    else:
        files_list = os.listdir(path)  #files da pasta
        files = ''
        nr_files = 0
        for i in files_list:
            newi = i.replace("''",'')
            ipath = path + '/' + newi
            itime = time.strftime('%d.%m.%Y %H:%M:%S', time.gmtime(os.path.getmtime(ipath)))
            files += ' ' + newi + ' ' + itime + ' ' + str(os.path.getsize(ipath))
            nr_files += 1
        message = 'BCK ' + msg + ' ' + str(nr_files) + files + '\n'
        data = contact_server(message)

        if (data[:7] == 'BKR EOF'):
            print '   Request cannot be answered\n'
        elif (data[:7] == 'BKR ERR'):
            print '   Request is not correctly formulated\n'
        else:
            process_data = (data[4:]).split(' ')
            ip   = process_data[0]
            port = process_data[1]

            #criar o socket e autenticar o user no bs
            bs_sock = contact_bs(ip, port)
            if (isinstance(bs_sock, str)):
                aut_error(bs_sock)
            else:
                #ENVIAR UPL + DIR + NR FICHEIROS
                i = 3
                files_to_backup = 0
                fich_list = []      # vai ser da forma [... , [nome ficheiro n, all info ficheiro n, tamanho fich] , ...]
                send_files = ''
                #este ciclo descobre o nr ficheiros e guarda a info dos ficheiros numa lista fich_list
                while (i < len(process_data)): #not sure about this (J)
                    fich = process_data[i] + ' ' + process_data[i+1] + ' ' + process_data[i+2] + ' ' + process_data[i+3]
                    fich_list += [[process_data[i], fich, process_data[i+3]]]
                    i += 4
                    files_to_backup += 1
                    send_files += fich
                upl_msg = 'UPL ' + msg + ' ' + str(files_to_backup)

                bs_sock.sendall(upl_msg)

                print '   Files to backup:'

                #ENVIAR INFO FICH + FICHEIRO
                for i in range(files_to_backup):
                    if (i == (files_to_backup-1)):
                        bs_sock.sendall((' ' + fich_list[i][1][:-1] + ' '))
                    else:
                        bs_sock.sendall((' ' + fich_list[i][1] + ' '))
                    # MANDAR FICHEIRO
                    f_open = path + '/' + fich_list[i][0]
                    print '    ' + fich_list[i][0]
                    f = open(f_open,'rb')
                    l = f.read(1) #sabemos que ele vai ler o nr de bytes do ficheiro!
                    bs_sock.sendall(l)
                    while (l != ''):
                        l = f.read(1)
                        bs_sock.sendall(l)
                    f.close()

                #DIZER AO BS QUE JA ENVIAMOS TUDO
                message = '\n'
                bs_sock.sendall(message)

                #RECEBER A RESPOSTA DO BS
                data = bs_sock.recv(BUFFER_SIZE)
                while (data[len(data)-1] != '\n'):
                    data = data + bs_sock.recv(BUFFER_SIZE)
                if(data.decode() == 'UPR OK\n'):
                    print '   Backup done\n'
                elif(data.decode() == 'UPR NOK\n'):
                    print '   Backup not done\n'
                else:
                    print '   Unknown error while backing up\n'

                bs_sock.close()



def restore(msg):
    message = 'RST' + msg + '\n'
    data = contact_server(message)
    print ' cs sends:' + data + '|'
    if (data == '-1' or data == '-2'):
        aut_error(data)
    elif(data == 'RSR EOF\n'):
        print '   Restore request cannot be answered\n'
    elif(data == 'RSR ERR\n'):
        print '   Restore request not correctly formulated\n'
    else:
        words   = data.split()
        ipbs    = words[1]
        portbs  = words[2]
        bs_sock = contact_bs(ipbs, portbs)

        #user manda o pedido de restore ao BS
        message = 'RSB' + msg + '\n'
        bs_sock.sendall(message)

        #o BS responde ao pedido
        data = bs_sock.recv(1) #procurar o \n, a msg acaba com \n
        while (len(data) != 7):
            data = data + bs_sock.recv(1)
        if(data == 'RBR EOF\n'):
            print '   Restore request cannot be answered\n'
        elif(data == 'RBR ERR\n'):
            print '   Restore request not correctly formulated\n'
        else:
            #create folder:
            folder_path = app_path() + '/' + msg[1:]
            if not (os.path.isdir(folder_path)):
                create_folder(folder_path)

            ligma = ''
            #discover number of files:
            data_split = data[4:].split(' ')
            if (len(data_split) > 1):      #1_a
                nr_files = data_split[0]
                ligma = data_split[1]

            elif (len(data_split) == 1 and data[6] == ' '):   #20_
                nr_files = data_split
            else:                         #910
                nr_files = data_split
                while(1):
                    data = bs_sock.recv(1)
                    if (data == ' '):
                        break
                    nr_files += data
            print '   Dir restored:\n' + '    ' + msg[1:] + '\n   Files restored:'#print restored directory

            for i in range(int(nr_files)):
                #read file description
                data = bs_sock.recv(1)  #data tem o carater lido

                fich = ligma + data

                data_split = fich.split(' ')
                while not (len(data_split) == 5 and data == ' '):
                    data = bs_sock.recv(1)
                    fich += data
                    data_split = fich.split(' ')
                print '    ' + data_split[0] #print restored file


                #create the file in our computer:
                path = folder_path + '/' + data_split[0]
                file = open(path, 'wb')

                ligma = ''

                #now we know the filesize, lets read the file
                filesize = int(data_split[3])
                data = bs_sock.recv(1)
                file.write(data)
                weve_read = 1
                while(weve_read != filesize):
                    data = bs_sock.recv(1)
                    file.write(data)
                    weve_read += 1
                data = bs_sock.recv(1)

                #store the content of the file in the file weve created
                file.close()

                date = data_split[1]
                hour = data_split[2]

                #sets modification time and access time of the backup file to the received file
                date = datetime(year=int(date[6:10]), month=int(date[3:5]), day=int(date[0:2]), hour=(int(hour[0:2])+1), minute=int(hour[3:5]), second=int(hour[6:8]))
                utime = time.mktime(date.timetuple())
                os.utime(path, (utime, utime))

            print '   Restore completed\n'



def dirlist():
    data  = contact_server('LSD\n')
    if (data == '-1' or data == '-2'):
        aut_error(data)
    else:
        size  = int(data[4])
        words = data[5:].split()
        for i in range(size):
            print '   ' + words[i]
        print



def filelist(msg):
    message = 'LSF' + msg + '\n'
    data = contact_server(message)
    if (data == '-1' or data == '-2'):
        aut_error(data)
    elif (data == 'LFD NOK\n'):
    	print '   Filelist request cannot be answered\n'
    else:
    	data_proc = data.split(' ')
    	nr_files = data_proc[3]
    	l=4
    	for i in range(int(nr_files)):
    		print '   ' + data_proc[l]
    		l+=4
    	print


def delete(msg):
    message = 'DEL' + msg + '\n'
    data = contact_server(message)
    if (data == '-1' or data == '-2'):
        aut_error(data)
    elif(data == 'DDR OK\n'):
        print '   Directory successfully deleted\n'
    elif(data == 'DDR NOK\n'):
        print '   Directory could not be deleted\n'



def logout():
    global curr_user, curr_pass, logged
    if (curr_user == 0):
    	print '   There is no logged user, logout request cannot be answered\n'
    else:
    	curr_user = 0
    	curr_pass = 0
    	logged = 0
    	print '   User successfully logged out\n'


#---------------------------------------------------------------------------------------------



#----5. MAIN----------------------------------------------------------------------------------
def main():
    while 1:
        message = raw_input()
        if(message[:5] == 'login'):
            if not (len(message) == 20):
                print '   Usage: login nnnnn pppppppp'
                print '          (where n is user number and p is user password)\n'

            else:
                login(message[5:])
        elif(check_login()):
            if(message == 'deluser'):
                deluser()
            elif(message[:6] == 'backup'):
                backup(message[7:])
            elif(message[:7] == 'restore'):
                restore(message[7:])
            elif(message == 'dirlist'):
                dirlist()
            elif(message[:8] == 'filelist'):
                if(message[8:] == ''):
                    print '   Filelist must be followed by a dir\n'
                else:
                    filelist(message[8:])
            elif(message[:6] == 'delete'):
                if(message[6:] == ''):
                    print '   Delete must be followed by a dir\n'
                else:
                    delete(message[6:])
            elif(message == 'logout'):
                logout()
            else:
                print 'ERR\n'
        elif(message[:4] == 'exit'):
            break
        else:
            print '   ERR\n'



#---------------------------------------------------------------------------------------------
main()
