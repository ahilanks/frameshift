// Run this in browser console to set up test data
const testData = {
  video: {
    name: 'test_video.mp4',
    size: 1024000,
    duration: 15.5,
    url: '/api/mock-video-blob',
    fileType: 'video/mp4'
  },
  preferences: {
    likes: ['Apple', 'Technology'],
    audience: ['tech-enthusiasts', 'young-adults'],
    selectedProducts: [{
      name: 'iPhone 15 Pro',
      description: 'Latest iPhone with titanium design',
      category: 'Technology'
    }]
  }
};

sessionStorage.setItem('frameshift-project', JSON.stringify(testData));
sessionStorage.setItem('frameshift-video-file', testData.video.url);

console.log('✅ Test data stored in sessionStorage');
console.log('📍 Navigate to /analysis to test');
console.log('📊 Data:', testData);