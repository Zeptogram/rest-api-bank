
# Sistemi Distribuiti - Progetto 2
### Autori
Progetto realizzato da:
- Elio Gargiulo - 869184
- Stefano Rigato - 869441

### Considerazioni
- É stato utilizzato un database MySQL strutturato con due tabelle: __account__ e __transazioni__.
- Le tabelle sono state create seguendo uno schema molto semplice ma adatto alle richieste.
- La tabella __account__ contiene l'accountId, name, surname e saldo di un account.
- La tabella __transazioni__ contiene il transactionId, from, to, amount, diverted, date.
- Un __deposito/prelievo__ è stato considerato come una transazione sullo stesso accountId.
- Esempio di un deposito nella tabella transazioni quindi sarà (gli id sono dei placeholder): 

``` sql
id | accountId1 | accountId1 |  10.00 |        0 | 2022-06-16 14:49:38 |
``` 

 - __Diverted__ indica tramite un 0/1 se la transazione è stata annullata o meno.
 - Si è optato per mantenere nella tabella __transazioni__ le transazioni degli account cancellati.
 - Opzionalmente si può testare l'applicazione anche attraverso questo link: https://imsteph.eu.pythonanywhere.com/

### Aggiunte (Endpoints):
- __/create__: Pagina html che permette l'aggiunta di account nel sistema.
- __/delete__: Pagina html che permette la cancellazione di un account dal sistema.
- __/deposit-withdraw__: Pagina html che permette di depositare/prelevare denaro. Se si utilizza la funzione di prelievo, non è necessario inserire il segno meno (che invece è chiesto nell'uso diretto della API).
- __/divert__: Pagina html che permette l'annullamento di una transazione.
- __/list__: Pagina html che mostra tutti gli account presenti nel sistema.
