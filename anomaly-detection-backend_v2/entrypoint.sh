#!/bin/sh
# Automatically convert Render's database URL format to JDBC format for Spring Boot
if [ -n "$DATABASE_URL" ]; then
  export SPRING_DATASOURCE_URL="jdbc:postgresql://${DATABASE_URL#*://}?sslmode=require"
fi

# Execute the main Java application container process
exec java -jar app.jar