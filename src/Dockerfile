
            #Use an appropriate base image
            FROM 
                            
            #Install pacakges
            RUN apt-get update && apt-get install -y \
                {packages}\
                && rm -rf /var/lib/apt/lists/*
            
            #Set working directory
            WORKDIR /app
                            
            #Copy application files into the container
            COPY . .
            
            #Expose port
            EXPOSE {exposed_port}
            
            #Define the startuo commnand
            CMD {cmd}                         
        