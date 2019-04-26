psql -U postgres -c "\du"

#psql -U postgres -c "ALTER USER \"$POSTGRESQL_USER\" WITH CREATEDB;"
createuser --createdb kiwi
