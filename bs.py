#--------------------------------------GRUPO 027----------------------------------------------
#							- Joao Tavares  86443
#							- Pedro Antunes 86493
#							- Rui Matos     79100
#---------------------------------------------------------------------------------------------


from   global_functions import *  #this file must be in the same directory as the main file!
from   socket import *
from   select  import select
from   datetime import datetime
import argparse
import os
import sys
import time
import shutil

BUFFER_SIZE = 1024

#How to execute different BSs:
#python2 ns.py -p xxxxx (chosen port)


#BS:
#1. Connection and Parsing
#2. Auxiliar Functions
#3. BS Functions (to support Client interaction)
#4. BS-CS Registration
#5. Client or User Handler (TCP/UDP request evaluation)
#
#7. Main




#----1. CONNECTION and PARSING----------------------------------------------------------------

   # DEFAULT
CS_IP = '127.0.0.1'		# DEFAULT usado para falar com o CS dentro do mm pc
CS_NAME = None
BS_PORT = 59000			# DEFAULT port
CS_PORT = 58027			# DEFAULT port


ip = socket(AF_INET, SOCK_DGRAM)
ip.connect(("8.8.8.8", 80))
BS_IP = ip.getsockname()[0]
ip.close()


parser = argparse.ArgumentParser()
parser.add_argument('-b', help='BSport: BS port')		# DEFAULT 59000
parser.add_argument('-n', help='CSname: client name')	# tejo
parser.add_argument('-p', help='CSport: client port')	# DEFAULT 58027 (58000 + group number)
args = parser.parse_args()

if(args.n != None):
	CS_NAME = args.n + '.ist.utl.pt'

if(args.b != None):
	BS_PORT = int(args.b)

if(args.p != None):
	CS_PORT = int(args.p)


#create UDP socket
s_udp = socket(AF_INET, SOCK_DGRAM)
s_udp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #evitar o errno98
s_udp.bind((BS_IP, BS_PORT))

# create TCP socket (talks with user)
s_tcp = socket(AF_INET,SOCK_STREAM)
s_tcp.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)   #evitar o errno98
s_tcp.bind(('', BS_PORT))
s_tcp.listen(1)

#---------------------------------------------------------------------------------------------


#----2. AUXILIAR FUNCTIONS--------------------------------------------------------------------
#---------------------------------------------------------------------------------------------


#----3. BS FUNCTIONS--------------------------------------------------------------------------

def add_user(user, passw, addr):
	filename = bs_user_folder(user) + '.txt' #user_nnnnn.txt

	if not (exists_file(filename)):  #se nao existir file desse user
		create_txt(filename, passw)
		create_folder(bs_user_folder(user))
		s_udp.sendto('LUR OK\n', addr)
		print 'New user: ' + user

	else:
   		s_udp.sendto('LUR NOK\n', addr)



def filelist(user, directory, addr):
	path = bs_user_folder(user) + '/' + directory.replace('\n', '')
	if(exists_file(path)):
		files_list = os.listdir(path)  #files da pasta
		files = ''
		nr_files = 0
		for i in files_list:
			newi = i.replace("''",'')
			ipath = path + '/' + newi
			itime = time.strftime('%d.%m.%Y %H:%M:%S', time.gmtime(os.path.getmtime(ipath)))
			files += ' ' + newi + ' ' + itime + ' ' + str(os.path.getsize(ipath))
			nr_files += 1
		message = 'LFD ' + str(nr_files) + files + '\n'
		s_udp.sendto(message, addr)
	else:
		message = 'LFD 0\n'
		s_udp.sendto(message, addr)


def delete(user, directory, addr):
	path = bs_user_folder(user) + '/' + directory.replace('\n', '')
	if not (exists_file(path)):
		s_udp.sendto('DBR NOK\n', addr)
	elif (is_path_empty(path)):
		os.rmdir(path)
		s_udp.sendto('DBR OK\n', addr)
	else:
		shutil.rmtree(path)
		s_udp.sendto('DBR OK\n', addr)


def confirm():
	# FALTA IMPLEMENTAR
	return 0		# quando recebe confirmacao do CS de que foi removido da lista ??



#---------------------------------------------------------------------------------------------


#----4. BS-CS REGISTRATION--------------------------------------------------------------------

#Register: registers BS in the CS
def register():
	global CS_IP
	global BS_IP
	global BS_PORT
	c_udp = socket(AF_INET, SOCK_DGRAM) # UDP
	if (CS_NAME != None):
	    CS_IP = gethostbyname(CS_NAME)
	message = 'REG ' + str(BS_IP) + ' ' + str(BS_PORT) + '\n'
	c_udp.sendto(message.encode(), (CS_IP, CS_PORT))

	rgr_reply, addr = c_udp.recvfrom(BUFFER_SIZE)
	if(rgr_reply.decode()[:6] == 'RGR OK'):
		print '   BS registered successfully\n'
	else:
		print '   Registration error\n'
	c_udp.close()

#---------------------------------------------------------------------------------------------


#----5. CLIENT or USER HANDLER----------------------------------------------------------------

def client_handler(data, addr):

	if(data[0:3]== 'LSU'):   #add user
		user_nr   = data[4:9]
		user_pass = data[10:19]
		add_user(user_nr, user_pass, addr)
	elif(data[0:3] == 'LSF'): #filelist
		user      = data[4:9]
		directory = data[10:]
		filelist(user, directory, addr)
	elif(data[0:3] == 'DLB'): #delete
		user = data[4:9]
		directory = data[10:]
		delete(user, directory, addr)
	elif(data[0:3] == 'UAR'): #restore
		confirm()
	elif(data[0:6] == 'bsTEST'): #restore
		test(addr)
	else:
		print 'ERR\n'



def user(s_tcp):
	conn, addr = s_tcp.accept()
	data = conn.recv(BUFFER_SIZE)
	if (data != ''):
		while (data[len(data)-1] != '\n'):
			data += conn.recv(BUFFER_SIZE)
	data.decode()

	user_name = user_authentication(data, conn, s_tcp)

	if(user_name != -1):
		data = conn.recv(1)
		while (len(data) != 4):
			data += conn.recv(1)

		if (data[0:3] == 'UPL'):
			upload(user_name, conn, addr)

		elif (data[0:3] == 'RSB'):
			restore(user_name, conn)

#---------------------------------------------------------------------------------------------






#----CLIENT FUNCTIONS-------------------------------------------------------------------------

def upload(user, conn, addr):
	#diretoria
	direct = ''
	data = conn.recv(1)
	while (data != ' '):
		direct += data
		data = conn.recv(1)

	#nr de ficheiros
	nr_files = ''
	data = conn.recv(1)
	while (data != ' '):
		nr_files += data
		data = conn.recv(1)

	#criar a pasta
	path = bs_user_folder(user) + '/' + direct
	if not(exists_file(path)):
		create_folder(path)

	#aqui comeca o tratamento de cada ficheiro
	for i in range(int(nr_files)):

		#nome e extensao
		name = ''
		data = conn.recv(1)
		while (data != ' '):
			name += data
			data = conn.recv(1)

		#cria o file
		path = bs_user_folder(user) + '/' + direct + '/' + name
		if(exists_file(path)):
			delete_txt(path)
		file = open(path, 'wb')

		#data
		date = ''
		data = conn.recv(1)
		while (data != ' '):
			date += data
			data = conn.recv(1)

		#hora
		hour = ''
		data =conn.recv(1)
		while (data != ' '):
			hour += data
			data = conn.recv(1)

		#nome e extensao
		file_size = ''
		data = conn.recv(1)
		while (data != ' '):
			file_size += data
			data = conn.recv(1)

		for l in range(int(file_size)):
			data = conn.recv(1)
			file.write(data)

		data = conn.recv(1) #ignore blank space
		file.close()

		#sets modification time and access time of the backup file to the received file
		date = datetime(year=int(date[6:10]), month=int(date[3:5]), day=int(date[0:2]), hour=(int(hour[0:2])+1), minute=int(hour[3:5]), second=int(hour[6:8]))
		utime = time.mktime(date.timetuple())
		os.utime(path, (utime, utime))

	conn.send('UPR OK\n')




def restore(user, conn):
	#data = directory
	direct = ''
	data = conn.recv(1)
	print data
	while (data != '\n'):
		direct += data
		data = conn.recv(1)
		print data


	path = bs_user_folder(user) + '/' + direct

	if not (exists_file(path)):
		conn.sendall('RBR EOF\n')
	elif (is_path_empty(path)):
		conn.sendall('RBR ERR\n')
	else:
		files_list = os.listdir(path)

		message = 'RBR ' + str(len(files_list))
		conn.sendall(message)

		for i in files_list:
			conn.sendall(' ')

			newi  = i.replace("''",'')
			conn.sendall(newi) #name
			conn.sendall(' ')

			ipath = path + '/' + newi

			itime = time.strftime('%d.%m.%Y %H:%M:%S', time.gmtime(os.path.getmtime(ipath)))
			conn.sendall(itime) #time
			conn.sendall(' ')

			isize = str(os.path.getsize(ipath))
			conn.sendall(isize) #size
			conn.sendall(' ')


			f = open(ipath, 'rb')
			l = f.read(1)
			conn.sendall(l)
			while(l != ''):
				l=f.read(1)
				conn.sendall(l)
			f.close()

			#se tivermos um stress com os tempos, e so fazer como no backup

		conn.sendall('\n')



#---------------------------------------------------------------------------------------------

#------server TCP-----------------------------------------------------------------------------
							#REGISTRATION AND AUTHENTICATION
#Interacao BS - Client
def user_authentication(data, conn, s_tcp):

	if(data[0:3] == 'AUT'):
		user = data[4:9],data[10:19]
		filename = bs_user_folder(user[0]) + '.txt'
		if (exists_file(filename)):
			if (read_first_line(filename) == user[1]):
				status = 1
			else:
				status = 2
		else:
			status = 2

		if status == 1:
			print 'User: ' + user[0]
			conn.send('AUR OK\n')
			return user[0]

		elif status == 2: #User Password is Wrong
			conn.send('AUR NOK\n')
			return -1

	else:
		print 'ERR\n'
		return -1

#---------------------------------------------------------------------------------------------





#----7. MAIN----------------------------------------------------------------------------------
#Funcao que processa o pedido tcp/udp no CS:
def main():
	folder_path = app_path() + '/BS'
	if not (os.path.isdir(folder_path)):
		create_folder(folder_path)

	register() #regista-se com o CS

	while 1:
		inS, _ , _ = select([s_tcp, s_udp],[],[])
		for s in inS:


			#TCP connection as server:
			if (s is s_tcp):
				pid = os.fork()
				if (pid == 0):       #FILHO
					#s_tcp.close()
					user(s_tcp)  #user divides in backup, restore and delete
                    #matar o filho


			#UDP Connection as server:
			elif (s is s_udp):
				data, addr = s_udp.recvfrom(BUFFER_SIZE)
				while (data[len(data)-1] != '\n'):
					data += conn.recvfrom(BUFFER_SIZE)

				pid = os.fork()
				if (pid == 0):       #FILHO
					client_handler(data,addr)  #data = msg toda que ele recebo por UDP
					#matar o filho

			else:
				print 'unknown socket: ' + s


#---------------------------------------------------------------------------------------------
main()
