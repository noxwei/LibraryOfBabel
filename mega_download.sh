#\!/bin/bash

echo "🎉 MEGA DOWNLOAD PARTY STARTING\!"
echo "📚 Processing 600 random books..."

counter=0
while IFS= read -r book || [[ -n "$book" ]]; do
    counter=$((counter + 1))
    echo "[$counter/600] ⏳ Downloading: $book"
    
    docker exec babels-archive-web python3 book_downloader.py "$book"
    
    echo "⏸️ Waiting 2 seconds..."
    sleep 2
    
    # Progress update every 25 books
    if [ $((counter % 25)) -eq 0 ]; then
        echo "🎊 Progress: $counter/600 books processed\!"
    fi
    
    # Stop at 500 successful downloads
    if [ $counter -eq 500 ]; then
        echo "🎯 Reached 500 downloads\! Stopping here."
        break
    fi
    
done < mega_book_list.txt

echo "🎉 MEGA DOWNLOAD PARTY COMPLETE\!"
echo "📚 Processed $counter books\!"
