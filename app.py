from flask import Flask, Response, render_template, request, jsonify
from MySQLController import MySQLController
from decimal import Decimal
import shortuuid
import json
import uuid
import re

app = Flask(__name__)

# Informazioni database
hostname = 'localhost'
username = 'root'
password = 'root'
database = 'banca'
db = MySQLController(hostname, username, password, database)

# Pagina principale
@app.route('/')
def home_page():
    return render_template('home.html')

# Pagina transfer
@app.route('/transfer')
def transfer_page():
    return render_template('transfer.html')

# Pagina deposita/prelieva
@app.route('/deposit-withdraw')
def deposit_withdraw_page():
    return render_template('deposit-withdraw.html')

# Pagina divert
@app.route('/divert')
def divert_page():
    return render_template('divert.html')

# Pagina create
@app.route('/create')
def create_page():
    return render_template('create.html')

# Pagina list
@app.route('/list')
def list_page():
    return render_template('list.html')

# Pagina delete
@app.route('/delete')
def delete_page():
    return render_template('delete.html')

# Servizio: /api/account
@app.route('/api/account', methods=['GET', 'POST', 'DELETE'])
def accountAll():
    # GET: Ritorna tutte le informazioni degli account in sistema
    if request.method == 'GET':
        db.connect()
        db.execute('SELECT account_id, name, surname, saldo  FROM account ORDER BY name')
        response = db.fetchall()
        if not response:
            db.close()
            return Response(status = 404)
        account = []
        for row in response:
            account.append ({ "accountId": row[0], "name": row[1], "surname": row[2], "saldo": str(row[3]) })
        db.close()
        return jsonify(account)
    # POST: Crea un nuovo account con i seguenti parametri: name, surname. 
    # Ritorna nel body l'accountId
    elif request.method == 'POST':
        params = json.loads(request.data)
        # Se i parametri non sono 2, ovvero quelli richiesti -> Bad Request
        if len(params) != 2:
            return Response(status = 400)
        if 'name' in params and 'surname' in params:
            accountId = shortuuid.ShortUUID(alphabet = "0123456789abcdef").random(length = 20)
            if checkWord(params['name']) and checkWord(params['surname']):
                db.connect()
                insert = 'INSERT INTO account (account_id, name, surname) VALUES (%s, %s, %s);'
                values = (accountId, params['name'], params['surname'])
                db.execute(insert, values)
                db.commit()
                db.close()
                return jsonify(accountId), 201
            else:
                return Response(status = 400)
        # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
        else:
            return Response(status = 400)
    # DELETE: Cancella l'account dal sistema tramite accountId passato in query string
    elif request.method == 'DELETE':
        accountId = request.args.get("id")
        if checkAccountId(accountId):
            db.connect()
            db.execute("SELECT account_id FROM account WHERE account_id = '%s'" % (accountId))
            query = db.fetchone()
            # Se la query non produce un risultato -> Not Found
            if not query:
                db.close()
                return Response(status = 404)
            db.execute("DELETE FROM account WHERE account_id = '%s'" % (accountId))
            db.commit()
            db.close()
            return jsonify(deleted=True)
        else:
            return Response(status = 400)

# Servizio: /api/account/<accountId>
@app.route('/api/account/<accountId>', methods=['GET', 'POST', 'PUT', 'PATCH', 'HEAD'])
def accountIdAll(accountId):
    # GET: Ritorna tutte le infomazioni di accountId e le transazioni effettuate
    if request.method == 'GET':
        db.connect()
        db.execute("SELECT name, surname, saldo FROM account WHERE account_id = '%s'" % (accountId))
        query = db.fetchone()
        # Se la query non produce un risultato -> Not Found
        if not query:
            db.close()
            return Response(status = 404)
        name = query[0]
        surname = query[1]
        saldo = str(query[2])
        db.execute("SELECT `transazioni`.* FROM `account`, `transazioni` WHERE `account_id` = '%s' AND `account_id` = `from` ORDER BY date ASC" % (accountId))
        query = db.fetchall()
        transazioni = []
        for row in query:
            transazioni.append ({ "transactionId": row[0], "from": row[1], "to": row[2], "amount": str(row[3]), "diverted": row[4], "date": str(row[5]) })
        account = ({ "name": name, "surname": surname, "saldo": saldo, "transazioni": transazioni})
        db.close()
        data = json.dumps(account)
        resp = Response(data, content_type='application/json; charset=utf-8')
        resp.headers['X-Sistema-Bancario'] = name + ";" + surname
        return resp
    # POST: Permette di effettuare versamenti e depositi nel saldo di accountId
    # con parametro: amount
    elif request.method == 'POST':
        params = json.loads(request.data)
        # Se i parametri non sono 1, ovvero da quelli richiesti -> Bad Request
        if len(params) != 1:
            return Response(status = 400)
        db.connect()
        db.execute("SELECT name, surname, saldo FROM account WHERE account_id = '%s'" % (accountId))
        query = db.fetchone()
        # Se la query non produce un risultato -> Not Found
        if not query:
            db.close()
            return Response(status = 404)
        if 'amount' in params:
            if checkAmount(params['amount']):
                amount = Decimal(params['amount'])
            # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
            else:
                return Response(status = 400)
            db.execute("SELECT saldo FROM account WHERE account_id = '%s'" % (accountId))
            query = db.fetchone()
            saldo_user = query[0]
            saldo_tot = saldo_user + Decimal(amount)
            if saldo_tot >= 0:
                transactionId = str(uuid.uuid4())
                db.execute("UPDATE account SET saldo = '%s' WHERE account_id = '%s'" % (saldo_tot, accountId))
                db.commit()
                db.execute("INSERT INTO `transazioni` (`transactionId`, `from`, `to`,`amount`) VALUES ('%s', '%s', '%s', %s);" % (transactionId, accountId, accountId, Decimal(amount)))
                db.commit()
                db.close()
                resp = ({"saldo": str(saldo_tot), "transactionId": transactionId})
                return jsonify(resp)
            # Se il saldo non è sufficiente (negativo) -> Forbidden
            else:
                db.close()
                return Response(status = 403)
        else:
            return Response(status = 400)
    # PUT: Aggiorna i parametri name e surname di accountId
    elif request.method == 'PUT':
        params = json.loads(request.data)
        # Se i parametri non sono 2, ovvero quelli richiesti -> Bad Request
        if len(params) != 2:
            return Response(status = 400)
        if 'name' in params and 'surname' in params:
            name = params['name']
            surname = params['surname']
            if checkWord(name) and checkWord(surname):
                db.connect()
                db.execute("UPDATE account SET name = '%s', surname = '%s' WHERE account_id = '%s'" % (name, surname, accountId))
                db.commit()
                db.close()
                return jsonify(updated=True)
            # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
            else:
                
                return Response(status = 400)
        else:
            return Response(status = 400) 
    # PATCH: Aggiorna un parametro tra name e surname di accountId
    elif request.method == 'PATCH':
        params = json.loads(request.data)
        # Se i parametri non sono 1, ovvero quelli richiesti -> Bad Request
        if len(params) != 1:
            return Response(status = 400)
        db.connect()
        if 'name' in params :
            name = params['name']
            if checkWord(name):
                db.execute("UPDATE account SET name = '%s' WHERE account_id = '%s'" % (name, accountId))
            else:
                return Response(status = 400)
        elif 'surname' in params:
            surname = params['surname']
            if checkWord(surname):
                db.execute("UPDATE account SET surname = '%s' WHERE account_id = '%s'" % (surname, accountId))
            else:
                return Response(status = 400)
        # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
        else:
            db.close()
            return Response(status = 400)
        db.commit()
        db.close()
        return jsonify(updated=True)
    # HEAD: Ritorna nell'header la coppia key: X-Sistema-Bancario value: name;surname
    elif request.method == 'HEAD':
        db.connect()
        db.execute("SELECT name, surname FROM account WHERE account_id = '%s'" % (accountId))
        query = db.fetchone()
        db.close()
        # Se la query non presenta nessun risultato -> Not Found
        if not query:
            return Response(status = 404)
        name = query[0]
        surname = query[1]
        resp = Response()
        resp.headers['X-Sistema-Bancario'] = name + ";" + surname
        return resp

# Servizio: /api/transfer
@app.route('/api/transfer', methods=['POST'])
def transfer():
    # POST: effettua un trasferimento da un accountId ad un altro tramite i parametri: 
    # from, to, amount
    if request.method == 'POST':
        params = json.loads(request.data)
        if 'from' in params and 'to' in params and 'amount' in params:  
            if params['from'] == params['to']:
                return jsonify(transfer="Errore: Stesso Account ID per Mittente e Destinatario!"), 422
            if checkAccountId(params['from']) and checkAccountId(params['to']):
                sender = params['from']
                receiver = params['to']
            else:
            # Se gli account non sono corretti -> Bad Request
                return Response(status = 400)
            if checkAmount(params['amount']):
                amount = Decimal(params['amount'])
                if amount <= 0:
                    return jsonify(transfer="Errore: Credito non valido!"), 422
            else:
            # Se l'amount non è corretto -> Bad Request
                return Response(status = 400)
        # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
        else:
            return Response(status = 400)
        db.connect()
        db.execute("SELECT saldo FROM account WHERE account_id = '%s'" % (sender))
        query = db.fetchone()
        # Se la query non presenta nessun risultato -> Not Found
        if not query:
            db.close()
            return Response(status = 404)
        saldo_sender = query[0]
        db.execute("SELECT saldo FROM account WHERE account_id = '%s'" % (receiver))
        query = db.fetchone()
        # Se la query non presenta nessun risultato -> Not Found
        if not query:
            db.close()
            return Response(status = 404)
        saldo_receiver = query[0]
        if saldo_sender < amount:
            db.close()
            return jsonify(transfer="Errore: Credito insufficiente"), 422
        new_saldo_sender = saldo_sender - amount
        db.execute("UPDATE account SET saldo = '%s' WHERE account_id = '%s'" % (new_saldo_sender, sender))
        db.commit()
        new_saldo_receiver = saldo_receiver + amount
        db.execute("UPDATE account SET saldo = '%s' WHERE account_id = '%s'" % (new_saldo_receiver, receiver))
        db.commit()
        transactionId = str(uuid.uuid4())
        db.execute("INSERT INTO `transazioni` (`transactionId`, `from`, `to`, `amount`) VALUES ('%s', '%s', '%s', %s);" % (transactionId, sender, receiver, amount))
        db.commit()
        db.close()
        return jsonify([{"accountId": sender, "saldo": str(new_saldo_sender), "transactionId": transactionId}, {"accountId": receiver, "saldo": str(new_saldo_receiver), "transactionId": transactionId}])

# Servizio: /api/divert
@app.route('/api/divert', methods=['POST'])
def divert():
    # POST: Annulla un transazione effettuata in precedenza tramite il parametro: id
    if request.method == 'POST':
        params = json.loads(request.data)
        # Se i parametri non sono 1, ovvero quelli richiesti -> Bad Request
        if len(params) != 1:
            return Response(status = 400)
        if 'id' in params:
            transactionIdToDivert = params['id']
            transactionId = str(uuid.uuid4())
            if checkTransactionId(transactionIdToDivert):
                db.connect()
                db.execute("SELECT `from`, `to`, `amount`, `diverted` FROM `transazioni` WHERE `transactionId` = '%s'" % transactionIdToDivert)
                query = db.fetchone()
                # Se la query non presenta nessun risultato -> Not Found
                if not query:
                    db.close()
                    return Response(status = 404)
                old_sender = query[0]
                old_receiver = query[1]
                # Se sto provando ad annullare una transazione di un prelievo/deposito (stesso accountId) -> Forbidden
                if old_sender == old_receiver:
                    db.close()
                    return Response(status = 403)
                amount = query[2]
                diverted = query[3]
                if diverted == 1:
                    db.close()
                    return jsonify(divert="Errore: Transazione già annullata in precedenza"), 422
                # Se non è presente il vecchio destinatario da errore 404
                db.execute("SELECT account_id FROM account WHERE account_id = '%s'" % (old_receiver))
                query = db.fetchone()
                if not query:
                    db.close()
                    return Response(status = 404)
                # Se non è presente il vecchio mittente da errore 404
                db.execute("SELECT account_id FROM account WHERE account_id = '%s'" % (old_sender))
                query = db.fetchone()
                if not query:
                    db.close()
                    return Response(status = 404)
                db.execute("SELECT saldo FROM account WHERE account_id = '%s'" % (old_receiver))
                query = db.fetchone()
                saldo_old_receiver = query[0]
                if saldo_old_receiver - amount < 0:
                    db.close()
                    return jsonify(divert="Errore: Operazione non disponibile dall'account del beneficiario precedente"), 422
                new_saldo_sender = saldo_old_receiver - amount
                db.execute("SELECT saldo FROM account WHERE account_id = '%s'" % (old_sender))
                query = db.fetchone()
                saldo_old_sender = query[0]
                new_saldo_receiver = saldo_old_sender + amount
                db.execute("UPDATE account SET saldo = '%s' WHERE account_id = '%s'" % (new_saldo_sender, old_receiver))
                db.commit()
                db.execute("UPDATE account SET saldo = '%s' WHERE account_id = '%s'" % (new_saldo_receiver, old_sender))
                db.commit()
                db.execute("INSERT INTO `transazioni` (`transactionId`, `from`, `to`,`amount`) VALUES ('%s', '%s', '%s', %s);" % (transactionId, old_receiver, old_sender, amount))
                db.commit()
                db.execute("UPDATE transazioni SET diverted = '1' WHERE transactionId = '%s'" % (transactionIdToDivert))
                db.commit()
                db.close()
                return jsonify([{"accountId": old_sender, "saldo": str(new_saldo_receiver), "transactionId": transactionId}, {"accountId": old_receiver, "saldo": str(new_saldo_sender), "transactionId": transactionId}])
            # Se il transactionId non è corretto -> Bad Request
            else:
                return Response(status = 400)
        # Se i parametri non sono corretti, ovvero quelli richiesti -> Bad Request
        else:
            return Response(status = 400)

# Controlla se l'argomento passato rispetta la sintassi di un accountId
def checkAccountId(id):
    return re.search("^[0-9a-f]{20}$", id)

# Controlla se l'argomento passato rispetta la sintassi di un transactionId
def checkTransactionId(id):
    return re.search("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", id)

# Controlla se l'argomento passato rispetta la sintassi di un amount
def checkAmount(a):
    return re.search("^(-\d+|-\d+\.\d{1,2}|\d+|\d+\.\d{1,2})$", str(a))

# Controlla se l'argomento passato rispetta la sintassi di una parola (name, surname)
def checkWord(w):
    return re.search("^\D*$", str(w))

# Avvio dell'applicazione
if __name__ == '__main__':
    app.run()
