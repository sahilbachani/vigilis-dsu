from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.db.models import Post, Source
from typing import Optional
import csv
import io
from io import BytesIO
from fastapi.responses import StreamingResponse, FileResponse
from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

router = APIRouter()

@router.get("/export")
def export_posts(format: str = Query("csv"), db: Session = Depends(get_db)):
    """
    Export flagged posts as CSV or PDF
    - format: 'csv' or 'pdf' (default: csv)
    """
    print(f"[EXPORT] Starting export with format: {format}")
    
    # Validate format
    if format not in ["csv", "pdf"]:
        print(f"[EXPORT] Invalid format: {format}")
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'pdf'")
    
    # Query flagged posts
    try:
        posts = db.query(Post).filter(Post.flagged == True).order_by(Post.timestamp.desc()).all()
        print(f"[EXPORT] Found {len(posts)} flagged posts")
        
        # Log first post details for debugging
        if posts:
            first = posts[0]
            print(f"[EXPORT] First post - ID: {first.post_id}, Author: {first.author}, URL: {first.url}, Category: {first.category}")
        
        if not posts:
            print(f"[EXPORT] No flagged posts found")
            if format == "csv":
                csv_header = "Post ID,Author,Content,Platform,Source,Flagged,Date,Post URL,Confidence Score\n"
                return StreamingResponse(
                    iter([csv_header.encode('utf-8')]),
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=flagged_posts_export.csv"}
                )
            else:
                return _export_pdf([])
        
        if format == "csv":
            print("[EXPORT] Exporting to CSV")
            return _export_csv(posts)
        else:
            print("[EXPORT] Exporting to PDF")
            return _export_pdf(posts)
            
    except Exception as e:
        print(f"[EXPORT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@router.get("/debug/info")
def debug_info(db: Session = Depends(get_db)):
    """Debug endpoint to check posts in database"""
    try:
        # Count total posts
        total_posts = db.query(Post).count()
        flagged_posts = db.query(Post).filter(Post.flagged == True).count()
        unflagged_posts = db.query(Post).filter(Post.flagged == False).count()
        posts_with_url = db.query(Post).filter(Post.url != None).filter(Post.url != "").count()
        
        print(f"[DEBUG] Total: {total_posts}, Flagged: {flagged_posts}, Unflagged: {unflagged_posts}, With URL: {posts_with_url}")
        
        # Get sample flagged posts
        sample_flagged = db.query(Post).filter(Post.flagged == True).limit(3).all()
        flagged_data = []
        for post in sample_flagged:
            flagged_data.append({
                "post_id": post.post_id,
                "author": post.author,
                "url": post.url,
                "category": post.category,
                "confidence_score": post.confidence_score,
                "flagged": post.flagged,
                "text_content": post.text_content[:50] if post.text_content else None
            })
        
        # Get sample all posts (to see if any have URLs)
        sample_all = db.query(Post).limit(5).all()
        all_data = []
        for post in sample_all:
            all_data.append({
                "post_id": post.post_id,
                "author": post.author,
                "url": post.url,
                "flagged": post.flagged
            })
        
        return {
            "total_posts": total_posts,
            "flagged_count": flagged_posts,
            "unflagged_count": unflagged_posts,
            "posts_with_urls": posts_with_url,
            "sample_flagged_posts": flagged_data,
            "sample_all_posts": all_data
        }
    except Exception as e:
        print(f"[DEBUG] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/debug/flag-all")
def flag_all_posts(db: Session = Depends(get_db)):
    """Debug endpoint to mark all posts as flagged for testing"""
    try:
        posts = db.query(Post).all()
        count = 0
        for post in posts:
            if not post.flagged:
                post.flagged = True
                count += 1
        db.commit()
        print(f"[DEBUG] Flagged {count} posts")
        return {"message": f"Flagged {count} posts for testing", "total_posts": len(posts)}
    except Exception as e:
        print(f"[DEBUG] Error: {str(e)}")
        return {"error": str(e)}

@router.post("/debug/populate-urls")
def populate_urls(db: Session = Depends(get_db)):
    """Debug endpoint to populate missing URLs in posts"""
    try:
        posts = db.query(Post).all()
        updated = 0
        
        for i, post in enumerate(posts):
            # Generate a URL if missing
            if not post.url or post.url.strip() == "":
                post.url = f"https://example.com/post/{post.post_id}"
                updated += 1
            
            # Add confidence score if missing
            if not post.confidence_score or post.confidence_score == 0.0:
                post.confidence_score = 0.75 + (i % 5) * 0.05  # Varies 0.75-0.95
            
            # Flag it for export testing
            post.flagged = True
        
        db.commit()
        print(f"[DEBUG] Updated {updated} posts with URLs and confidence scores")
        return {
            "message": f"Updated {updated} posts",
            "total_processed": len(posts),
            "all_flagged": True
        }
    except Exception as e:
        print(f"[DEBUG] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.get("/scraped")
def get_scraped_posts(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=500)
):
    """
    Get all scraped posts from all platforms (twitter, facebook, tiktok, website)
    """
    return (
        db.query(Post)
        .filter(Post.category.in_(["twitter", "facebook", "tiktok", "website"]))
        .order_by(Post.timestamp.desc())
        .limit(limit)
        .all()
    )

@router.get("/")
def get_posts(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=500)
):
    """
    Get posts with optional filtering
    - category: Filter by category (e.g., 'twitter', 'facebook', 'website')
    - limit: Number of results (max 500)
    """
    query = db.query(Post).order_by(Post.timestamp.desc())
    
    if category:
        query = query.filter(Post.category == category)
    
    return query.limit(limit).all()

@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    return db.query(Post).filter(Post.post_id == post_id).first()

@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post by ID"""
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully", "post_id": post_id}


@router.delete("/")
def delete_posts_by_source(
    source_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Delete all posts from a specific source by source_id"""
    posts = db.query(Post).filter(Post.source_id == source_id).all()
    
    if not posts:
        return {"message": "No posts found for this source", "deleted_count": 0}
    
    deleted_count = len(posts)
    for post in posts:
        db.delete(post)
    
    db.commit()
    return {"message": f"Deleted {deleted_count} posts", "deleted_count": deleted_count, "source_id": source_id}

def _export_csv(posts):
    """Export posts as CSV/Excel"""
    try:
        print(f"[CSV_EXPORT] Starting CSV export for {len(posts)} posts")
        
        # Create CSV in memory
        text_output = io.StringIO()
        writer = csv.writer(text_output)
        
        # Write header
        writer.writerow([
            "Post ID",
            "Author",
            "Content",
            "Platform",
            "Source",
            "Flagged",
            "Date",
            "Post URL",
            "Confidence Score"
        ])
        
        print("[CSV_EXPORT] Header written")
        
        # Write data rows
        rows_written = 0
        for post in posts:
            try:
                # Safe source name extraction
                source_name = "Unknown"
                if post.source:
                    source_name = post.source.source_name
                elif post.category:
                    source_name = post.category
                
                # Safe URL extraction
                post_url = str(post.url) if post.url else ""
                
                # Safe confidence extraction
                confidence = post.confidence_score if post.confidence_score else 0.0
                confidence_str = f"{confidence:.2f}"
                
                # Safe timestamp
                date_str = post.timestamp.strftime("%d/%m/%Y %H:%M") if post.timestamp else ""
                
                writer.writerow([
                    post.post_id,
                    post.author or "Unknown",
                    (post.text_content or "")[:200],
                    post.category or "Unknown",
                    source_name,
                    "Yes" if post.flagged else "No",
                    date_str,
                    post_url,
                    confidence_str
                ])
                rows_written += 1
                
            except Exception as row_error:
                print(f"[CSV_EXPORT] Error writing row for post {post.post_id}: {str(row_error)}")
                continue
        
        print(f"[CSV_EXPORT] Wrote {rows_written} data rows")
        
        # Convert to bytes
        csv_content = text_output.getvalue().encode('utf-8')
        print(f"[CSV_EXPORT] CSV content size: {len(csv_content)} bytes")
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=flagged_posts_export.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        print(f"[CSV_EXPORT] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def _export_pdf(posts):
    """Export posts as PDF"""
    try:
        print(f"[PDF_EXPORT] Starting PDF export for {len(posts)} posts")
        
        if not REPORTLAB_AVAILABLE:
            raise Exception("reportlab not available")
        
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title = Paragraph("Flagged Posts Report", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Build table data
        table_data = [["ID", "Author", "Platform", "Source", "Date", "Score", "URL"]]
        
        rows_added = 0
        for post in posts[:50]:  # Limit to 50
            try:
                # Safe source name
                source_name = "Unknown"
                if post.source:
                    source_name = post.source.source_name
                elif post.category:
                    source_name = post.category
                
                # Safe URL
                post_url = str(post.url)[:30] if post.url else "N/A"
                
                # Safe confidence
                confidence = post.confidence_score if post.confidence_score else 0.0
                conf_str = f"{confidence:.2f}"
                
                # Safe timestamp
                date_str = post.timestamp.strftime("%m/%d %H:%M") if post.timestamp else ""
                
                table_data.append([
                    str(post.post_id),
                    str(post.author)[:15] if post.author else "Unknown",
                    str(post.category)[:12] if post.category else "Unknown",
                    str(source_name)[:12],
                    date_str,
                    conf_str,
                    post_url
                ])
                rows_added += 1
                
            except Exception as row_error:
                print(f"[PDF_EXPORT] Error processing post {post.post_id}: {str(row_error)}")
                continue
        
        print(f"[PDF_EXPORT] Added {rows_added} rows to table")
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        
        # Build PDF
        print("[PDF_EXPORT] Building PDF document")
        doc.build(elements)
        
        pdf_value = output.getvalue()
        output.close()
        
        print(f"[PDF_EXPORT] PDF created, size: {len(pdf_value)} bytes")
        
        return StreamingResponse(
            iter([pdf_value]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=flagged_posts_export.pdf"}
        )
        
    except Exception as e:
        print(f"[PDF_EXPORT] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")


@router.patch("/{post_id}/mark-reviewed")
def mark_post_reviewed(post_id: int, db: Session = Depends(get_db)):
    """Mark a post as reviewed"""
    post = db.query(Post).filter(Post.post_id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Update post status (add reviewed flag if exists, or just mark timestamp)
    if hasattr(post, 'is_reviewed'):
        post.is_reviewed = True
    if hasattr(post, 'reviewed_at'):
        post.reviewed_at = datetime.utcnow()
    
    db.commit()
    return {"status": "reviewed", "post_id": post_id, "message": "Post marked as reviewed"}
