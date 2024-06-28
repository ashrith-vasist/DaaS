
            #Use an appropriate base image
            FROM python 3:9 -slime
                            
            #Install pacakges
            RUN apt-get update && apt-get install -y \
                nginx\
                && rm -rf /var/lib/apt/lists/*
            
            #Set working directory
            WORKDIR /app
                            
            #Copy application files into the container
            COPY . .
            
            #Expose port
            EXPOSE 8080
            
            #Define the startuo commnand
            CMD python3 app.py                         
        