

from os import chdir, listdir, mkdir
from time import mktime, gmtime, strptime, ctime
from math import log, exp

folders = []
count = 0
for item in listdir():
    if item.find('.') == -1:
        folders.append(item)
        print(count + 1, ' - ', item)
        count += 1

while True:
    path_index = int(input('choose folder with LV logs: ')) - 1

    if path_index in range(len(folders)):
        path = folders[path_index]
        break
    else:
        print('incorrect input')
        
while True:
    choice = input('''1 - required current integral;
2 - required Sr-22 activity at the EOB;
3 - required Sr-22 activity at the calibration datetime.
calculate approximate EOB datetime for: ''')

    if choice == '1':
        desired = float(input('enter required current integral at the EOB (mkAh): '))
        break
    elif choice == '2':
        desired = float(input('enter required activity at the EOB (mCi): '))
        break
    elif choice == '3':
        desired = float(input('enter required activity at the calibration datetime (mCi): '))
        break
    else:
        print('incorrect input')


        
files = listdir(path)
chdir(path)

#popravka na poteri
K = 0.82

Y = 0.537
h_l = 25.5
la = 0

#print(files)


def calc_seconds(datetime):

    return mktime(strptime(datetime, "%d.%m.%Y %H:%M:%S"))


def extract_file(filename, l = []):

    f = open(filename, 'r')
    r = f.read().splitlines()
    
    for i in range(len(r)):
        rr = r[i].split()
        try:
            current = float('.'.join(rr[-2].split(',')))
            if current != 0:
                l.append([calc_seconds((rr[0] + ' ' + rr[1])), current])
        except:
            continue

    return l

#print(extract_file('Rb_7-14-00A.txt'))

def calc_lambda(h_l):
    return log(2)/(h_l*24*3600)


def calc_activity(last_time, line, la):
    I = line[1]
    t = last_time - line[0]

    return (I * Y * (5/3600)) * exp(-la * t) * K

def calc_at_calib_activity(cal_date, last_time, A, la):

     return A * exp(-la * (cal_date - last_time))


def predict_EOB(desired, last_time, start_time, A, int_I, cal_date):
    mean_I = int_I * 3600 / (last_time - start_time)
    temp_time = last_time

    if choice =='1':

        dt = (desired - int_I) * 3600 / mean_I
        A = (mean_I * Y * K / (la * 3600)) * (1 - exp(-la * dt)) + A * exp(-la * dt)
        int_I = desired


    elif choice == '2':

        dt = (-log((desired - mean_I * Y * K / (la * 3600)) /
                   (A - mean_I * Y * K / (la * 3600))) / la)
        A = desired
        int_I += mean_I * dt / 3600

    elif choice == '3':
        beta = (mean_I * Y * K) / (la * 3600)
        #print(desired, ' ', cal_date, ' ', last_time, ' ', A, ' ', beta, ' ', la)
        dt = log((desired * exp(la * (cal_date - last_time)) - A + beta) / beta) / la
        int_I += mean_I * dt / 3600
        A = (mean_I * Y * K / (la * 3600)) * (1 - exp(-la * dt)) + A * exp(-la * dt)

        
        
    EOB = last_time + dt
    A_cal = calc_at_calib_activity(cal_date, EOB, A, la)
    
    return EOB, mean_I, int_I, A, A_cal

      
def main():

    global la
    A = 0
    int_I = 0
    l = []
    for f in files:
        
        if (f[-11:-8] != 'ava') and f.endswith('txt'):
            extract_file(f, l)

    l.sort()

###popravka
#    start_fail = calc_seconds("10.11.2015 16:20:00")
#    end_fail = calc_seconds("11.11.2015 10:10:00")
#    miss_int_I = 500
#    mean_I = miss_int_I * 3600/(end_fail - start_fail)

#    time = l[-1][0]
#    if time > start_fail:
#        t = start_fail
#        while t < end_fail and t < time:
#            l.append([t, mean_I])
#            t += 5
#        l.sort()
        
    
    start_time = l[0][0]
    last_time = l[-1][0]
    cal_date = calc_seconds("11.12.2015 12:00:00")

    la = calc_lambda(h_l)
    print(la)
    

    for i in l:
        A += calc_activity(last_time, i, la)
        int_I += i[1]*(5/3600)
   
    A_cal = calc_at_calib_activity(cal_date, last_time, A, la)
    try:
        mkdir('Result')
    except:
        print('Warning: "Result/" already exists!')
        
    f = open('Result/predicted_EOB.txt', 'w')
    f.write('Beginning of the irradiation: ' + ctime(start_time) + '\n')
    f.write('Last data obtained at: ' + ctime(last_time) + '\n')
    f.write('Integrated current = ' + str(int_I) + ' mkAh\n')
    f.write('Calculated Sr-82 activity at the last data time: ' + str(A) + ' mCi\n')
    f.write('Expected activity at the ' + ctime(cal_date) + ' : ' + str(A_cal) + ' mCi\n')



    print('--------------------------')
    print('\nIntegrated current: ', int_I, ' mkAh')
    print('\nBeginning of the irradiation: ', ctime(start_time))      
    print('\nLast data obtained at: ', ctime(last_time))
    print('\nCalculated Sr-82 activity at the last data time: ', A, 'mCi\n')
    print('Expected activity at the ', ctime(cal_date), ' : ',A_cal, ' mCi\n')


    EOB, mean_I, int_I, A, A_cal = predict_EOB(desired, last_time, start_time, A, int_I, cal_date)

    f.write('\nMean current: ' + str(mean_I) + ' mkA\n')
    f.write('\nPredicted datetime of EOB: ' + ctime(EOB))
    f.write('\nSr-82 activity at the EOB: ' + str(A) + ' mCi\n')
    f.write('Integrated current at the EOB = ' + str(int_I) + ' mkAh\n')
    f.write('Expected activity at the ' + ctime(cal_date) + ' : ' + str(A_cal) + ' mCi\n')
    f.close()

    print('\nMean current: ', mean_I, ' mkA\n')
    print('\nPredicted datetime of EOB: ', ctime(EOB))
    print('\nSr-82 activity at the EOB: ', A, ' mCi\n')
    print('Integrated current at the EOB = ', int_I, ' mkAh\n')
    print('Expected activity at the ', ctime(cal_date), ' : ',A_cal, ' mCi\n')
    input()


if __name__ == '__main__':
    main()
        
            








    
    

    


