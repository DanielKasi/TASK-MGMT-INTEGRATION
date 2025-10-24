import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">
            Task Management Module
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            Standalone development mode for the Task Management module
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Link 
              href="/dashboard" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Dashboard</h3>
              <p className="text-gray-600">View project overview and analytics</p>
            </Link>
            
            <Link 
              href="/projects" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Projects</h3>
              <p className="text-gray-600">Manage projects and tasks</p>
            </Link>
            
            <Link 
              href="/task-mgt/task" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Task Management</h3>
              <p className="text-gray-600">Create and manage tasks</p>
            </Link>
            
            <Link 
              href="/admin" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Admin</h3>
              <p className="text-gray-600">Administrative settings</p>
            </Link>
            
            <Link 
              href="/analytics/project" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Analytics</h3>
              <p className="text-gray-600">Project analytics and reports</p>
            </Link>
            
            <Link 
              href="/login" 
              className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Authentication</h3>
              <p className="text-gray-600">Login and user management</p>
            </Link>
          </div>
          
          <div className="mt-12 p-6 bg-blue-50 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              Development Mode
            </h3>
            <p className="text-blue-700">
              This is the standalone version of the Task Management module. 
              In production, this module will be integrated into the main platform.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
