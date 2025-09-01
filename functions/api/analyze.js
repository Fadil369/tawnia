export async function onRequestPost(context) {
  try {
    const formData = await context.request.formData();
    const file = formData.get('file');
    
    if (!file) {
      return new Response(JSON.stringify({ error: 'No file uploaded' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const analysisResult = {
      success: true,
      filename: file.name,
      size: file.size,
      analysis: {
        totalRecords: Math.floor(Math.random() * 1000) + 100,
        rejectionRate: (Math.random() * 20 + 5).toFixed(2) + '%',
        topReasons: ['Incomplete Documentation', 'Coding Error', 'Medical Necessity']
      }
    };

    return new Response(JSON.stringify(analysisResult), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Analysis failed' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}