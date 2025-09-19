print("O programa funciona?")
sim = "SIM"
resp = input()  


def ja_foi_tutoria():
    print("Já foi na tutoria?")
    resp = input()
    if resp == sim:
        print("Choremos!")
    else:
        print("Temos um time a disposição!")



if resp == sim:
    print("Você entende o que fez?")
    resp = input()
    if resp == sim:
        print("Ótimo. Então não mexe!")
    else:
        ja_foi_tutoria()
else:
    print("Você sabe onde está o erro?")
    resp = input()
    if resp == sim:
        print("Acha que pode solucionar sozinho?")
        resp = input()
        if resp == sim:
            print("Então mão na massa!")
        else:
            print("Já pesquisou no google?")
            resp = input()
            if resp == sim:
                ja_foi_tutoria()
            else:
                print("Corre lá então!")
    else:
        ja_foi_tutoria()